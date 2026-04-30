package com.stockanalyzer.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.LocalDateTime;

@Entity
@Table(name = "signals")
@Data
@NoArgsConstructor
@AllArgsConstructor
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
    private String market;  // "US", "AR", "EU", "JP"
    
    @Column(nullable = false)
    private LocalDateTime analyzedAt;
    
    private LocalDateTime createdAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
