package com.stockanalyzer.service;

import com.stockanalyzer.model.Stock;

import java.util.List;
import java.util.Optional;

public interface IStockService {
    
    List<Stock> getAllStocks();
    
    Optional<Stock> getStockBySymbol(String symbol);
    
    void initDefaultStocks();
    
    Stock createOrUpdateStock(String symbol, String market, String name, 
                             String sector, String industry, String exchange, 
                             String country, String logoUrl, Long marketCap);
}