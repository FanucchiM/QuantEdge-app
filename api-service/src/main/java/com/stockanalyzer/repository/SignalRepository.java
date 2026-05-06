package com.stockanalyzer.repository;

import com.stockanalyzer.model.Signal;
import com.stockanalyzer.model.Stock;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface SignalRepository extends JpaRepository<Signal, Long> {
    
    @Query("SELECT s FROM Signal s JOIN FETCH s.stock WHERE s.analyzedAt >= :startDate")
    List<Signal> findByAnalyzedAtAfterWithStock(LocalDateTime startDate);
    
    @Query("SELECT s FROM Signal s JOIN FETCH s.stock WHERE s.analyzedAt >= :startDate")
    Page<Signal> findByAnalyzedAtAfter(LocalDateTime startDate, Pageable pageable);
    
    Optional<Signal> findTopByStockOrderByAnalyzedAtDesc(Stock stock);
    
    @Query("SELECT s FROM Signal s WHERE DATE(s.analyzedAt) = DATE(:date)")
    List<Signal> findByAnalyzedAtDate(LocalDateTime date);

    @Query("SELECT s FROM Signal s JOIN FETCH s.stock WHERE s.stock.symbol = :symbol ORDER BY s.analyzedAt DESC LIMIT 1")
    com.stockanalyzer.model.Signal findTopBySymbolOrderByAnalyzedAtDesc(@Param("symbol") String symbol);

    void deleteByStock(Stock stock);
    
    @org.springframework.transaction.annotation.Transactional
    int deleteByAnalyzedAtAfter(LocalDateTime startDate);
}
