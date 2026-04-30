package com.stockanalyzer.dto;

import jakarta.validation.constraints.*;
import java.time.LocalDateTime;

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
    
    public SignalRequestDTO() {}
    
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public String getMarket() { return market; }
    public void setMarket(String market) { this.market = market; }
    public String getSignalType() { return signalType; }
    public void setSignalType(String signalType) { this.signalType = signalType; }
    public Double getRsi() { return rsi; }
    public void setRsi(Double rsi) { this.rsi = rsi; }
    public Double getEma20() { return ema20; }
    public void setEma20(Double ema20) { this.ema20 = ema20; }
    public Double getEma50() { return ema50; }
    public void setEma50(Double ema50) { this.ema50 = ema50; }
    public Double getMacd() { return macd; }
    public void setMacd(Double macd) { this.macd = macd; }
    public Double getAtr() { return atr; }
    public void setAtr(Double atr) { this.atr = atr; }
    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }
    public Double getPriceChange24h() { return priceChange24h; }
    public void setPriceChange24h(Double priceChange24h) { this.priceChange24h = priceChange24h; }
    public Double getPriceChangePercent24h() { return priceChangePercent24h; }
    public void setPriceChangePercent24h(Double priceChangePercent24h) { this.priceChangePercent24h = priceChangePercent24h; }
    public Double getVolumeRelative() { return volumeRelative; }
    public void setVolumeRelative(Double volumeRelative) { this.volumeRelative = volumeRelative; }
    public String getTrend() { return trend; }
    public void setTrend(String trend) { this.trend = trend; }
    public String getExplanation() { return explanation; }
    public void setExplanation(String explanation) { this.explanation = explanation; }
    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }
    public String getReasons() { return reasons; }
    public void setReasons(String reasons) { this.reasons = reasons; }
    public String getCompanyName() { return companyName; }
    public void setCompanyName(String companyName) { this.companyName = companyName; }
    public String getSector() { return sector; }
    public void setSector(String sector) { this.sector = sector; }
    public String getIndustry() { return industry; }
    public void setIndustry(String industry) { this.industry = industry; }
    public String getExchange() { return exchange; }
    public void setExchange(String exchange) { this.exchange = exchange; }
    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }
    public String getLogoUrl() { return logoUrl; }
    public void setLogoUrl(String logoUrl) { this.logoUrl = logoUrl; }
    public Long getMarketCap() { return marketCap; }
    public void setMarketCap(Long marketCap) { this.marketCap = marketCap; }
    public LocalDateTime getAnalyzedAt() { return analyzedAt; }
    public void setAnalyzedAt(LocalDateTime analyzedAt) { this.analyzedAt = analyzedAt; }
}