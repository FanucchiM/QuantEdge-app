package com.stockanalyzer.dto;

public class StockHistoryDto {

    private String symbol;
    private String date;
    private Double closePrice;
    private Double ema20;
    private Double ema50;
    private Double rsi;
    private Double high;
    private Double low;
    private Double volume;

    public StockHistoryDto() {}

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }
    public Double getClosePrice() { return closePrice; }
    public void setClosePrice(Double closePrice) { this.closePrice = closePrice; }
    public Double getEma20() { return ema20; }
    public void setEma20(Double ema20) { this.ema20 = ema20; }
    public Double getEma50() { return ema50; }
    public void setEma50(Double ema50) { this.ema50 = ema50; }
    public Double getRsi() { return rsi; }
    public void setRsi(Double rsi) { this.rsi = rsi; }
    public Double getHigh() { return high; }
    public void setHigh(Double high) { this.high = high; }
    public Double getLow() { return low; }
    public void setLow(Double low) { this.low = low; }
    public Double getVolume() { return volume; }
    public void setVolume(Double volume) { this.volume = volume; }
}