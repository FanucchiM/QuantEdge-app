package com.stockanalyzer.controller;

import com.stockanalyzer.dto.StockHistoryDto;
import com.stockanalyzer.model.Signal;
import com.stockanalyzer.model.StockHistory;
import com.stockanalyzer.repository.SignalRepository;
import com.stockanalyzer.repository.StockHistoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Controller for stock history data.
 * Replaces Python /stock/{symbol}/history endpoint.
 * Data comes from stock_history table (filled by Python batch).
 */
@RestController
@RequestMapping("/api/stocks")
public class StockHistoryController {

    @Autowired
    private StockHistoryRepository historyRepository;

    @Autowired
    private SignalRepository signalRepository;

    /**
     * GET /api/stocks/{symbol}/history?days=60
     * Returns historical chart data + current signal info.
     */
    @GetMapping("/{symbol}/history")
    public ResponseEntity<?> getHistory(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "60") int days) {

        String sym = symbol.toUpperCase();
        LocalDate since = LocalDate.now().minusDays(days);

        List<StockHistory> rows = historyRepository
                .findBySymbolAndDateAfterOrderByDateAsc(sym, since);

        if (rows.isEmpty()) {
            return ResponseEntity.status(404)
                    .body(Map.of("error", "No history found for " + sym));
        }

        // Chart data arrays
        List<String> dates = new ArrayList<>();
        List<Double> prices = new ArrayList<>();
        List<Double> ema20 = new ArrayList<>();
        List<Double> ema50 = new ArrayList<>();
        List<Double> rsi = new ArrayList<>();

        for (StockHistory row : rows) {
            dates.add(row.getDate().toString());
            prices.add(round2(row.getClosePrice()));
            ema20.add(round2(row.getEma20()));
            ema50.add(round2(row.getEma50()));
            rsi.add(round2(row.getRsi()));
        }

        // Current and previous prices for change calculation
        StockHistory last = rows.get(rows.size() - 1);
        StockHistory prev = rows.size() >= 2 ? rows.get(rows.size() - 2) : last;

        double currentPrice = last.getClosePrice();
        double prevClose = prev.getClosePrice();
        double change24h = currentPrice - prevClose;
        double changePct24h = prevClose > 0 ? (change24h / prevClose) * 100 : 0;

        // 52w high/low
        double high52w = rows.stream()
                .mapToDouble(r -> r.getHigh() != null ? r.getHigh() : 0)
                .max().orElse(0);
        double low52w = rows.stream()
                .mapToDouble(r -> r.getLow() != null ? r.getLow() : 0)
                .min().orElse(0);

        // Latest signal from signals table
        Signal latestSignal = signalRepository.findTopBySymbolOrderByAnalyzedAtDesc(sym);

        Map<String, Object> signalGenerated = new HashMap<>();
        String signalType = "NEUTRAL";
        String signalTypeResult = "NEUTRAL";

        double currentRsi = rsi.isEmpty() ? 50 : rsi.get(rsi.size() - 1);

        if (latestSignal != null) {
            signalTypeResult = latestSignal.getSignalType();
            signalGenerated.put("date", latestSignal.getAnalyzedAt().toLocalDate().toString());
            signalGenerated.put("atPrice", latestSignal.getPrice());
            signalGenerated.put("rsi", latestSignal.getRsi());

            String trend = latestSignal.getTrend();
            if (currentRsi < 30 && "BEARISH".equals(trend)) {
                signalType = "OVERSOLD_REVERSAL";
            } else if (currentRsi > 70 && "BULLISH".equals(trend)) {
                signalType = "OVERBOUGHT_CORRECTION";
            } else if ("BUY".equals(signalTypeResult)) {
                signalType = "BULLISH_TREND";
            } else if ("SELL".equals(signalTypeResult)) {
                signalType = "BEARISH_TREND";
            }

            signalGenerated.put("type", signalType);
        }

        // Build full response matching Python format
        Map<String, Object> result = new HashMap<>();
        result.put("symbol", sym);
        result.put("companyName", latestSignal != null ? latestSignal.getCompanyName() : sym);
        result.put("logoUrl", latestSignal != null ? latestSignal.getLogoUrl() : "");
        result.put("market", latestSignal != null ? latestSignal.getMarket() : "");
        result.put("signalType", signalTypeResult);
        result.put("currentPrice", round2(currentPrice));
        result.put("priceChange24h", round2(change24h));
        result.put("priceChangePercent24h", round2(changePct24h));
        result.put("high52w", round2(high52w));
        result.put("low52w", round2(low52w));
        result.put("signalGenerated", signalGenerated);
        result.put("sector", latestSignal != null ? latestSignal.getSector() : null);
        result.put("industry", latestSignal != null ? latestSignal.getIndustry() : null);
        result.put("exchange", latestSignal != null ? latestSignal.getExchange() : null);
        result.put("country", latestSignal != null ? latestSignal.getCountry() : null);
        result.put("marketCap", latestSignal != null ? latestSignal.getMarketCap() : null);

        Map<String, Object> chartData = new HashMap<>();
        chartData.put("dates", dates);
        chartData.put("price", prices);
        chartData.put("ema20", ema20);
        chartData.put("ema50", ema50);
        chartData.put("rsi", rsi);
        result.put("chartData", chartData);

        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/stocks/{symbol}/history/batch
     * Called by Python during batch to save historical data.
     */
    @PostMapping("/{symbol}/history/batch")
    @Transactional
    public ResponseEntity<?> saveBatch(
            @PathVariable String symbol,
            @RequestBody List<StockHistoryDto> rows) {

        String sym = symbol.toUpperCase();

        // Delete old data first
        historyRepository.deleteBySymbol(sym);

        // Insert new data
        List<StockHistory> entities = new ArrayList<>();
        for (StockHistoryDto dto : rows) {
            StockHistory h = new StockHistory();
            h.setSymbol(sym);
            h.setDate(LocalDate.parse(dto.getDate()));
            h.setClosePrice(dto.getClosePrice());
            h.setEma20(dto.getEma20());
            h.setEma50(dto.getEma50());
            h.setRsi(dto.getRsi());
            h.setHigh(dto.getHigh());
            h.setLow(dto.getLow());
            h.setVolume(dto.getVolume());
            entities.add(h);
        }

        historyRepository.saveAll(entities);
        return ResponseEntity.ok(Map.of("saved", entities.size()));
    }

    /**
     * GET /api/stocks/{symbol}/seasonality?years=2026,2025,2024
     * Calculate monthly historical performance from stock_history.
     */
    @GetMapping("/{symbol}/seasonality")
    public ResponseEntity<?> getSeasonality(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "2026,2025,2024") String years) {

        String sym = symbol.toUpperCase();

        List<Integer> yearList = Arrays.stream(years.split(","))
                .map(String::trim)
                .map(Integer::parseInt)
                .collect(Collectors.toList());

        List<StockHistory> rows = historyRepository.findBySymbolOrderByDateAsc(sym);

        if (rows.isEmpty()) {
            return ResponseEntity.status(404)
                    .body(Map.of("error", "No history found for " + sym));
        }

        String[] monthNames = {"Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"};
        int currentYear = LocalDate.now().getYear();
        int currentMonth = LocalDate.now().getMonthValue();

        Map<String, List<Double> yearlyReturns = new LinkedHashMap<>();

        for (int year : yearList) {
            int lastMonth = (year == currentYear) ? currentMonth : 12;
            List<Double> monthlyReturns = new ArrayList<>();

            for (int month = 1; month <= lastMonth; month++) {
                final int y = year, m = month;

                List<Double> monthPrices = rows.stream()
                        .filter(r -> r.getDate().getYear() == y && r.getDate().getMonthValue() == m)
                        .map(StockHistory::getClosePrice)
                        .filter(p -> p != null && p > 0)
                        .collect(Collectors.toList());

                if (monthPrices.size() < 2) {
                    monthlyReturns.add(0.0);
                    continue;
                }

                double first = monthPrices.get(0);
                double last = monthPrices.get(monthPrices.size() - 1);
                double ret = ((last - first) / first) * 100;
                monthlyReturns.add(round2(ret));
            }

            yearlyReturns.put(String.valueOf(year), monthlyReturns);
        }

        int maxMonths = yearlyReturns.values().stream()
                .mapToInt(List::size).max().orElse(0);

        List<Double> avgReturns = new ArrayList<>();
        for (int i = 0; i < maxMonths; i++) {
            final int idx = i;
            List<Double> vals = yearlyReturns.values().stream()
                    .filter(l -> idx < l.size())
                    .map(l -> l.get(idx))
                    .collect(Collectors.toList());

            double avg = vals.isEmpty() ? 0.0
                    : vals.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            avgReturns.add(round2(avg));
        }

        List<String> months = Arrays.asList(monthNames).subList(0, maxMonths);

        double bestVal = avgReturns.isEmpty() ? 0 : Collections.max(avgReturns);
        double worstVal = avgReturns.isEmpty() ? 0 : Collections.min(avgReturns);
        String bestMonth = avgReturns.isEmpty() ? null : months.get(avgReturns.indexOf(bestVal));
        String worstMonth = avgReturns.isEmpty() ? null : months.get(avgReturns.indexOf(worstVal));
        double avgReturn = avgReturns.isEmpty() ? 0
                : round2(avgReturns.stream().mapToDouble(Double::doubleValue).average().orElse(0));

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("years", yearList.stream().map(String::valueOf).collect(Collectors.toList()));
        result.put("yearlyReturns", yearlyReturns);
        result.put("monthlyAvg", avgReturns);
        result.put("months", months);
        result.put("bestMonth", bestMonth);
        result.put("worstMonth", worstMonth);
        result.put("avgReturn", avgReturn);

        return ResponseEntity.ok(result);
    }

    private double round2(Double value) {
        if (value == null) return 0.0;
        return Math.round(value * 100.0) / 100.0;
    }
}