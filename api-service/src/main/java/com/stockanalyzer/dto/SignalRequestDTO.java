package com.stockanalyzer.dto;

import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import jakarta.validation.constraints.*;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SignalRequestDTO {
    
    @NotBlank(message = "Symbol is required")
    @Size(min = 1, max = 10, message = "Symbol must be 1-10 characters")
    @Pattern(regexp = "^[A-Z0-9\\.]+$", message = "Symbol must be uppercase letters, numbers, or dots")
    private String symbol;
    
    @NotBlank(message = "Market is required")
    @Pattern(regexp = "^(AR|US|EU|JP)$", message = "Market must be AR, US, EU, or JP")
    private String market;
    
    @NotBlank(message = "Signal type is required")
    @Pattern(regexp = "^(BUY|SELL|HOLD)$", message = "Signal type must be BUY, SELL, or HOLD")
    private String signalType;
    
    @DecimalMin(value = "0.0", message = "RSI must be at least 0")
    @DecimalMax(value = "100.0", message = "RSI must be at most 100")
    private Double rsi;
    
    private Double ema20;
    private Double ema50;
    private Double macd;
    private Double atr;
    private Double price;
    private Double priceChange24h;
    private Double priceChangePercent24h;
    private Double volumeRelative;
    
    @Pattern(regexp = "^(BULLISH|BEARISH|LATERAL)$", message = "Trend must be BULLISH, BEARISH, or LATERAL")
    private String trend;
    
    private String explanation;
    private String summary;
    private String reasons;
    private String companyName;
    private String sector;
    private String industry;
    private String exchange;
    private String country;
    private String logoUrl;
    private Long marketCap;
    private LocalDateTime analyzedAt;
}
