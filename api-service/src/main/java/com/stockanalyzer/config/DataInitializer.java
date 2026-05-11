package com.stockanalyzer.config;

import com.stockanalyzer.service.IStockService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class DataInitializer implements CommandLineRunner {
    private final IStockService stockService;
    
    public DataInitializer(IStockService stockService) {
        this.stockService = stockService;
    }
    
    @Override
    public void run(String... args) {
        stockService.initDefaultStocks();
    }
}
