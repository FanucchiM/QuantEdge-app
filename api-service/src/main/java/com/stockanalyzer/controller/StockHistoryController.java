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

    private double round2(double value) {
        if (value == null) return 0.0;
        return Math.round(value * 100.0) / 100.0;
    }
}