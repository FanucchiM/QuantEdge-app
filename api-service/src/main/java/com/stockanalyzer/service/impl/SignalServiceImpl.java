package com.stockanalyzer.service.impl;

import com.stockanalyzer.dto.SignalDTO;
import com.stockanalyzer.dto.SignalRequestDTO;
import com.stockanalyzer.model.Signal;
import com.stockanalyzer.model.Stock;
import com.stockanalyzer.repository.SignalRepository;
import com.stockanalyzer.service.IStockService;
import com.stockanalyzer.service.ISignalService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class SignalServiceImpl implements ISignalService {
    
    private static final Logger log = LoggerFactory.getLogger(SignalServiceImpl.class);
    
    private final SignalRepository signalRepository;
    private final IStockService stockService;
    
    public SignalServiceImpl(SignalRepository signalRepository, IStockService stockService) {
        this.signalRepository = signalRepository;
        this.stockService = stockService;
    }
    
    @Override
    @Transactional(readOnly = true)
    public List<SignalDTO> getTodaySignals() {
        LocalDateTime startOfDay = LocalDate.now().atStartOfDay();
        List<Signal> signals = signalRepository.findByAnalyzedAtAfterWithStock(startOfDay);
        Map<String, Integer> marketOrder = Map.of("AR", 0, "US", 1, "EU", 2, "JP", 3);
        signals.sort((a, b) -> {
            String marketA = a.getStock().getMarket() != null ? a.getStock().getMarket() : "US";
            String marketB = b.getStock().getMarket() != null ? b.getStock().getMarket() : "US";
            int orderA = marketOrder.getOrDefault(marketA, 99);
            int orderB = marketOrder.getOrDefault(marketB, 99);
            if (orderA != orderB) return Integer.compare(orderA, orderB);
            return a.getStock().getSymbol().compareTo(b.getStock().getSymbol());
        });
        return signals.stream().map(this::toDTO).collect(Collectors.toList());
    }
    
    @Override
    @Transactional(readOnly = true)
    public Page<SignalDTO> getTodaySignalsPaginated(Pageable pageable) {
        LocalDateTime startOfDay = LocalDate.now().atStartOfDay();
        Page<Signal> signalsPage = signalRepository.findByAnalyzedAtAfter(startOfDay, pageable);
        return signalsPage.map(this::toDTO);
    }
    
    @Value("${app.signal.history-days:365}")
    private int signalHistoryDays;
    
    @Override
    @Transactional(readOnly = true)
    public Page<SignalDTO> getSignalHistory(Pageable pageable) {
        LocalDateTime startOfDay = LocalDate.now().minusDays(signalHistoryDays).atStartOfDay();
        return signalRepository.findByAnalyzedAtAfter(startOfDay, pageable).map(this::toDTO);
    }
    
    @Override
    @Transactional(readOnly = true)
    public SignalDTO getLatestSignalBySymbol(String symbol) {
        Stock stock = stockService.getStockBySymbol(symbol).orElse(null);
        if (stock == null) return null;
        
        Signal signal = signalRepository.findTopByStockOrderByAnalyzedAtDesc(stock).orElse(null);
        return signal != null ? toDTO(signal) : null;
    }
    
    @Override
    @Transactional
    public SignalDTO saveSignal(SignalRequestDTO requestDTO) {
        Stock stock = stockService.createOrUpdateStock(
            requestDTO.getSymbol(),
            requestDTO.getMarket(),
            requestDTO.getCompanyName(),
            requestDTO.getSector(),
            requestDTO.getIndustry(),
            requestDTO.getExchange(),
            requestDTO.getCountry(),
            requestDTO.getLogoUrl(),
            requestDTO.getMarketCap()
        );
        
        Signal signal = new Signal();
        signal.setStock(stock);
        signal.setSignalType(requestDTO.getSignalType());
        signal.setRsi(requestDTO.getRsi());
        signal.setEma20(requestDTO.getEma20());
        signal.setEma50(requestDTO.getEma50());
        signal.setMacd(requestDTO.getMacd());
        signal.setAtr(requestDTO.getAtr());
        signal.setPrice(requestDTO.getPrice());
        signal.setPriceChange24h(requestDTO.getPriceChange24h());
        signal.setPriceChangePercent24h(requestDTO.getPriceChangePercent24h());
        signal.setVolumeRelative(requestDTO.getVolumeRelative());
        signal.setTrend(requestDTO.getTrend());
        signal.setExplanation(requestDTO.getExplanation());
        signal.setSummary(requestDTO.getSummary());
        signal.setReasons(requestDTO.getReasons());
        signal.setMarket(requestDTO.getMarket());
        signal.setAnalyzedAt(requestDTO.getAnalyzedAt());
        
        Signal saved = signalRepository.save(signal);
        return toDTO(saved);
    }
    
    @Override
    @Transactional
    public List<SignalDTO> saveSignals(List<SignalRequestDTO> requests) {
        for (SignalRequestDTO request : requests) {
            Stock stock = stockService.getStockBySymbol(request.getSymbol()).orElse(null);
            if (stock != null) {
                signalRepository.deleteByStock(stock);
            }
        }
        return requests.stream()
                .map(this::saveSignal)
                .collect(Collectors.toList());
    }
    
    @Override
    @Transactional
    public int deleteTodaySignals() {
        LocalDateTime startOfDay = LocalDate.now().atStartOfDay();
        return signalRepository.deleteByAnalyzedAtAfter(startOfDay);
    }
    
    private SignalDTO toDTO(Signal signal) {
        Stock stock = signal.getStock();
        return SignalDTO.builder()
                .id(signal.getId())
                .symbol(stock.getSymbol())
                .market(stock.getMarket())
                .signalType(signal.getSignalType())
                .rsi(signal.getRsi())
                .ema20(signal.getEma20())
                .ema50(signal.getEma50())
                .macd(signal.getMacd())
                .atr(signal.getAtr())
                .price(signal.getPrice())
                .priceChange24h(signal.getPriceChange24h())
                .priceChangePercent24h(signal.getPriceChangePercent24h())
                .volumeRelative(signal.getVolumeRelative())
                .trend(signal.getTrend())
                .explanation(signal.getExplanation())
                .summary(signal.getSummary())
                .reasons(signal.getReasons())
                .companyName(stock.getName())
                .sector(stock.getSector())
                .industry(stock.getIndustry())
                .exchange(stock.getExchange())
                .country(stock.getCountry())
                .logoUrl(stock.getLogoUrl())
                .marketCap(stock.getMarketCap())
                .analyzedAt(signal.getAnalyzedAt())
                .build();
    }
}