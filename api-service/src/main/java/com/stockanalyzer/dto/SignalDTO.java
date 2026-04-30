package com.stockanalyzer.dto;

import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SignalDTO {
    private Long id;
    private String symbol;
    private String market;
    private String signalType;
    private Double rsi;
    private Double ema20;
    private Double ema50;
    private Double macd;
    private Double atr;
    private Double price;
    private Double priceChange24h;
    private Double priceChangePercent24h;
    private Double volumeRelative;
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
