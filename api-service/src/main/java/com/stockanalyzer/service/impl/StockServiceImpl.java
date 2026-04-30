package com.stockanalyzer.service.impl;

import com.stockanalyzer.config.StockConfig;
import com.stockanalyzer.model.Stock;
import com.stockanalyzer.repository.StockRepository;
import com.stockanalyzer.service.IStockService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class StockServiceImpl implements IStockService {
    
    private final StockRepository stockRepository;
    
    public StockServiceImpl(StockRepository stockRepository) {
        this.stockRepository = stockRepository;
    }
    
    @Override
    @Transactional(readOnly = true)
    public List<Stock> getAllStocks() {
        return stockRepository.findAll();
    }
    
    @Override
    @Transactional(readOnly = true)
    public Optional<Stock> getStockBySymbol(String symbol) {
        return stockRepository.findBySymbol(symbol);
    }
    
    @Override
    @Transactional
    public void initDefaultStocks() {
        StockConfig.US_STOCKS.forEach(stock -> {
            if (!stockRepository.existsBySymbol(stock.get("symbol"))) {
                createOrUpdateStock(stock.get("symbol"), "US", stock.get("name"), null, null, null, null, null, null);
            }
        });
        
        StockConfig.AR_STOCKS.forEach(stock -> {
            if (!stockRepository.existsBySymbol(stock.get("symbol"))) {
                createOrUpdateStock(stock.get("symbol"), "AR", stock.get("name"), null, null, null, null, null, null);
            }
        });

        StockConfig.EU_STOCKS.forEach(stock -> {
            if (!stockRepository.existsBySymbol(stock.get("symbol"))) {
                createOrUpdateStock(stock.get("symbol"), "EU", stock.get("name"), null, null, null, null, null, null);
            }
        });

        StockConfig.JP_STOCKS.forEach(stock -> {
            if (!stockRepository.existsBySymbol(stock.get("symbol"))) {
                createOrUpdateStock(stock.get("symbol"), "JP", stock.get("name"), null, null, null, null, null, null);
            }
        });
    }

    @Override
    @Transactional
    public Stock createOrUpdateStock(String symbol, String market, String name, 
                                      String sector, String industry, String exchange, 
                                      String country, String logoUrl, Long marketCap) {
        Optional<Stock> existingStock = stockRepository.findBySymbol(symbol);
        if (existingStock.isPresent()) {
            Stock stock = existingStock.get();
            stock.setMarket(market);
            if (name != null) stock.setName(name);
            if (sector != null) stock.setSector(sector);
            if (industry != null) stock.setIndustry(industry);
            if (exchange != null) stock.setExchange(exchange);
            if (country != null) stock.setCountry(country);
            if (logoUrl != null) stock.setLogoUrl(logoUrl);
            if (marketCap != null) stock.setMarketCap(marketCap);
            return stockRepository.save(stock);
        } else {
            Stock newStock = new Stock();
            newStock.setSymbol(symbol);
            newStock.setMarket(market);
            newStock.setName(name);
            newStock.setSector(sector);
            newStock.setIndustry(industry);
            newStock.setExchange(exchange);
            newStock.setCountry(country);
            newStock.setLogoUrl(logoUrl);
            newStock.setMarketCap(marketCap);
            return stockRepository.save(newStock);
        }
    }
}
