package com.stockanalyzer.controller;

import com.stockanalyzer.model.Stock;
import com.stockanalyzer.service.IStockService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/stocks")
@CrossOrigin(origins = "*")
public class StockController {
    private final IStockService stockService;
    private final RestTemplate restTemplate;
    
    @Value("${analytics.service.url:http://localhost:8000}")
    private String analyticsUrl;
    
    public StockController(IStockService stockService, RestTemplate restTemplate) {
        this.stockService = stockService;
        this.restTemplate = restTemplate;
    }
    
    @GetMapping
    public ResponseEntity<List<Stock>> getAllStocks() {
        return ResponseEntity.ok(stockService.getAllStocks());
    }
    
    @GetMapping("/{symbol}")
    public ResponseEntity<Stock> getStock(@PathVariable String symbol) {
        return stockService.getStockBySymbol(symbol)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
    
    @GetMapping("/{symbol}/history")
    public ResponseEntity<?> getStockHistory(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "60") int days) {
        try {
            String url = analyticsUrl + "/stock/" + symbol + "/history?days=" + days;
            ResponseEntity<Map> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                null,
                Map.class
            );
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of("error", "Analytics service unavailable: " + e.getMessage()));
        }
    }
    
    @GetMapping("/{symbol}/seasonality")
    public ResponseEntity<?> getStockSeasonality(
            @PathVariable String symbol,
            @RequestParam(defaultValue = "2026,2025,2024") String years) {
        try {
            String url = analyticsUrl + "/stock/" + symbol + "/seasonality?years=" + years;
            ResponseEntity<Object> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                null,
                Object.class
            );
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of("error", "Analytics service unavailable: " + e.getMessage()));
        }
    }
}
