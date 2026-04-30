package com.stockanalyzer.dto;

import java.time.LocalDateTime;

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
    
    public SignalDTO() {}
    
    public SignalDTO(Long id, String symbol, String market, String signalType, Double rsi,
            Double ema20, Double ema50, Double macd, Double atr, Double price,
            Double priceChange24h, Double priceChangePercent24h, Double volumeRelative,
            String trend, String explanation, String summary, String reasons,
            String companyName, String sector, String industry, String exchange,
            String country, String logoUrl, Long marketCap, LocalDateTime analyzedAt) {
        this.id = id;
        this.symbol = symbol;
        this.market = market;
        this.signalType = signalType;
        this.rsi = rsi;
        this.ema20 = ema20;
        this.ema50 = ema50;
        this.macd = macd;
        this.atr = atr;
        this.price = price;
        this.priceChange24h = priceChange24h;
        this.priceChangePercent24h = priceChangePercent24h;
        this.volumeRelative = volumeRelative;
        this.trend = trend;
        this.explanation = explanation;
        this.summary = summary;
        this.reasons = reasons;
        this.companyName = companyName;
        this.sector = sector;
        this.industry = industry;
        this.exchange = exchange;
        this.country = country;
        this.logoUrl = logoUrl;
        this.marketCap = marketCap;
        this.analyzedAt = analyzedAt;
    }
    
    public static SignalDTOBuilder builder() {
        return new SignalDTOBuilder();
    }
    
    public static class SignalDTOBuilder {
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
        
        public SignalDTOBuilder id(Long id) { this.id = id; return this; }
        public SignalDTOBuilder symbol(String symbol) { this.symbol = symbol; return this; }
        public SignalDTOBuilder market(String market) { this.market = market; return this; }
        public SignalDTOBuilder signalType(String signalType) { this.signalType = signalType; return this; }
        public SignalDTOBuilder rsi(Double rsi) { this.rsi = rsi; return this; }
        public SignalDTOBuilder ema20(Double ema20) { this.ema20 = ema20; return this; }
        public SignalDTOBuilder ema50(Double ema50) { this.ema50 = ema50; return this; }
        public SignalDTOBuilder macd(Double macd) { this.macd = macd; return this; }
        public SignalDTOBuilder atr(Double atr) { this.atr = atr; return this; }
        public SignalDTOBuilder price(Double price) { this.price = price; return this; }
        public SignalDTOBuilder priceChange24h(Double priceChange24h) { this.priceChange24h = priceChange24h; return this; }
        public SignalDTOBuilder priceChangePercent24h(Double priceChangePercent24h) { this.priceChangePercent24h = priceChangePercent24h; return this; }
        public SignalDTOBuilder volumeRelative(Double volumeRelative) { this.volumeRelative = volumeRelative; return this; }
        public SignalDTOBuilder trend(String trend) { this.trend = trend; return this; }
        public SignalDTOBuilder explanation(String explanation) { this.explanation = explanation; return this; }
        public SignalDTOBuilder summary(String summary) { this.summary = summary; return this; }
        public SignalDTOBuilder reasons(String reasons) { this.reasons = reasons; return this; }
        public SignalDTOBuilder companyName(String companyName) { this.companyName = companyName; return this; }
        public SignalDTOBuilder sector(String sector) { this.sector = sector; return this; }
        public SignalDTOBuilder industry(String industry) { this.industry = industry; return this; }
        public SignalDTOBuilder exchange(String exchange) { this.exchange = exchange; return this; }
        public SignalDTOBuilder country(String country) { this.country = country; return this; }
        public SignalDTOBuilder logoUrl(String logoUrl) { this.logoUrl = logoUrl; return this; }
        public SignalDTOBuilder marketCap(Long marketCap) { this.marketCap = marketCap; return this; }
        public SignalDTOBuilder analyzedAt(LocalDateTime analyzedAt) { this.analyzedAt = analyzedAt; return this; }
        
        public SignalDTO build() {
            SignalDTO dto = new SignalDTO();
            dto.id = this.id;
            dto.symbol = this.symbol;
            dto.market = this.market;
            dto.signalType = this.signalType;
            dto.rsi = this.rsi;
            dto.ema20 = this.ema20;
            dto.ema50 = this.ema50;
            dto.macd = this.macd;
            dto.atr = this.atr;
            dto.price = this.price;
            dto.priceChange24h = this.priceChange24h;
            dto.priceChangePercent24h = this.priceChangePercent24h;
            dto.volumeRelative = this.volumeRelative;
            dto.trend = this.trend;
            dto.explanation = this.explanation;
            dto.summary = this.summary;
            dto.reasons = this.reasons;
            dto.companyName = this.companyName;
            dto.sector = this.sector;
            dto.industry = this.industry;
            dto.exchange = this.exchange;
            dto.country = this.country;
            dto.logoUrl = this.logoUrl;
            dto.marketCap = this.marketCap;
            dto.analyzedAt = this.analyzedAt;
            return dto;
        }
    }
    
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
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