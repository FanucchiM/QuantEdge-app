package com.stockanalyzer.repository;

import com.stockanalyzer.model.StockHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface StockHistoryRepository extends JpaRepository<StockHistory, Long> {

    List<StockHistory> findBySymbolAndDateAfterOrderByDateAsc(String symbol, LocalDate since);

    @Modifying
    @Transactional
    @Query("DELETE FROM StockHistory h WHERE h.symbol = :symbol")
    void deleteBySymbol(@Param("symbol") String symbol);
}