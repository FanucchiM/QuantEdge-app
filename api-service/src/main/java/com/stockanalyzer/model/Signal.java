package com.stockanalyzer.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "signals")
public class Signal {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "stock_id", nullable = false)
    private Stock stock;
    
    @Column(nullable = false)
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
    @Column(columnDefinition = "TEXT")
    private String reasons;
    private String companyName;
    
    private String sector;
    private String industry;
    private String exchange;
    private String country;
    private String logoUrl;
    private Long marketCap;
    
    @Column(length = 2)
    private String market;
    
    @Column(nullable = false)
    private LocalDateTime analyzedAt;
    
    private LocalDateTime createdAt;
    
    public Signal() {}
    
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Stock getStock() { return stock; }
    public void setStock(Stock stock) { this.stock = stock; }
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
    public String getMarket() { return market; }
    public void setMarket(String market) { this.market = market; }
    public LocalDateTime getAnalyzedAt() { return analyzedAt; }
    public void setAnalyzedAt(LocalDateTime analyzedAt) { this.analyzedAt = analyzedAt; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}