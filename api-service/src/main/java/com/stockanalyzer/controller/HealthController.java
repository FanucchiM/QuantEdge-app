package com.stockanalyzer.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.CrossOrigin;
import java.time.LocalDateTime;
import java.util.Map;

@RestController
@CrossOrigin(origins = "*", allowedHeaders = "*", methods = {org.springframework.http.HttpMethod.GET, org.springframework.http.HttpMethod.POST, org.springframework.http.HttpMethod.PUT, org.springframework.http.HttpMethod.DELETE, org.springframework.http.HttpMethod.OPTIONS})
public class HealthController {
    
    @GetMapping("/api/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "UP",
                "service", "Stock Analyzer API",
                "timestamp", LocalDateTime.now().toString()
        ));
    }
}
