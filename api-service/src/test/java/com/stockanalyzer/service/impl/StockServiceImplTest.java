package com.stockanalyzer.service.impl;

import com.stockanalyzer.model.Stock;
import com.stockanalyzer.repository.StockRepository;
import com.stockanalyzer.service.IStockService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class StockServiceImplTest {

    @Mock
    private StockRepository stockRepository;

    @InjectMocks
    private StockServiceImpl stockService;

    private Stock testStock;

    @BeforeEach
    void setUp() {
        testStock = new Stock();
        testStock.setId(1L);
        testStock.setSymbol("AAPL");
        testStock.setMarket("US");
        testStock.setName("Apple Inc.");
    }

    @Nested
    @DisplayName("getStockBySymbol")
    class GetStockBySymbolTests {

        @Test
        @DisplayName("returns stock when found")
        void getStockBySymbol_found_returnsStock() {
            when(stockRepository.findBySymbol("AAPL")).thenReturn(Optional.of(testStock));

            Optional<Stock> result = stockService.getStockBySymbol("AAPL");

            assertThat(result).isPresent();
            assertThat(result.get().getSymbol()).isEqualTo("AAPL");
            verify(stockRepository).findBySymbol("AAPL");
        }

        @Test
        @DisplayName("returns empty when not found")
        void getStockBySymbol_notFound_returnsEmpty() {
            when(stockRepository.findBySymbol("UNKNOWN")).thenReturn(Optional.empty());

            Optional<Stock> result = stockService.getStockBySymbol("UNKNOWN");

            assertThat(result).isEmpty();
            verify(stockRepository).findBySymbol("UNKNOWN");
        }
    }

    @Nested
    @DisplayName("getAllStocks")
    class GetAllStocksTests {

        @Test
        @DisplayName("returns all stocks from repository")
        void getAllStocks_returnsAllStocks() {
            Stock anotherStock = new Stock();
            anotherStock.setId(2L);
            anotherStock.setSymbol("MSFT");
            anotherStock.setMarket("US");

            when(stockRepository.findAll()).thenReturn(List.of(testStock, anotherStock));

            List<Stock> result = stockService.getAllStocks();

            assertThat(result).hasSize(2);
            assertThat(result.get(0).getSymbol()).isEqualTo("AAPL");
            assertThat(result.get(1).getSymbol()).isEqualTo("MSFT");
            verify(stockRepository).findAll();
        }
    }

    @Nested
    @DisplayName("createOrUpdateStock")
    class CreateOrUpdateStockTests {

        @Test
        @DisplayName("creates new stock when symbol does not exist")
        void createOrUpdateStock_createsNew() {
            when(stockRepository.findBySymbol("AAPL")).thenReturn(Optional.empty());
            when(stockRepository.save(any(Stock.class))).thenAnswer(invocation -> {
                Stock saved = invocation.getArgument(0);
                saved.setId(1L);
                return saved;
            });

            Stock result = stockService.createOrUpdateStock(
                    "AAPL", "US", "Apple Inc.", "Technology",
                    "Consumer Electronics", "NASDAQ", "USA",
                    "https://logo.url", 3000000000L
            );

            assertThat(result.getId()).isEqualTo(1L);
            assertThat(result.getSymbol()).isEqualTo("AAPL");
            assertThat(result.getName()).isEqualTo("Apple Inc.");

            ArgumentCaptor<Stock> captor = ArgumentCaptor.forClass(Stock.class);
            verify(stockRepository).save(captor.capture());
            Stock savedStock = captor.getValue();
            assertThat(savedStock.getSymbol()).isEqualTo("AAPL");
            assertThat(savedStock.getMarket()).isEqualTo("US");
            assertThat(savedStock.getName()).isEqualTo("Apple Inc.");
            assertThat(savedStock.getSector()).isEqualTo("Technology");
            assertThat(savedStock.getIndustry()).isEqualTo("Consumer Electronics");
            assertThat(savedStock.getExchange()).isEqualTo("NASDAQ");
            assertThat(savedStock.getCountry()).isEqualTo("USA");
            assertThat(savedStock.getLogoUrl()).isEqualTo("https://logo.url");
            assertThat(savedStock.getMarketCap()).isEqualTo(3000000000L);
        }

        @Test
        @DisplayName("updates existing stock when symbol exists")
        void createOrUpdateStock_updatesExisting() {
            when(stockRepository.findBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

            Stock result = stockService.createOrUpdateStock(
                    "AAPL", "US", "Apple Inc. Updated", "Technology Updated",
                    null, null, null, null, null
            );

            assertThat(result.getSymbol()).isEqualTo("AAPL");
            assertThat(result.getMarket()).isEqualTo("US");

            verify(stockRepository).findBySymbol("AAPL");
            verify(stockRepository).save(testStock);

            assertThat(testStock.getName()).isEqualTo("Apple Inc. Updated");
            assertThat(testStock.getSector()).isEqualTo("Technology Updated");
        }

        @Test
        @DisplayName("does not overwrite existing fields with null values")
        void createOrUpdateStock_doesNotOverwriteWithNulls() {
            testStock.setName("Apple Inc.");
            testStock.setSector("Technology");
            testStock.setIndustry("Consumer Electronics");
            testStock.setExchange("NASDAQ");
            testStock.setCountry("USA");
            testStock.setLogoUrl("https://logo.url");
            testStock.setMarketCap(3000000000L);

            when(stockRepository.findBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

            stockService.createOrUpdateStock(
                    "AAPL", "US", null, null, null, null, null, null, null
            );

            assertThat(testStock.getName()).isEqualTo("Apple Inc.");
            assertThat(testStock.getSector()).isEqualTo("Technology");
            assertThat(testStock.getIndustry()).isEqualTo("Consumer Electronics");
            assertThat(testStock.getExchange()).isEqualTo("NASDAQ");
            assertThat(testStock.getCountry()).isEqualTo("USA");
            assertThat(testStock.getLogoUrl()).isEqualTo("https://logo.url");
            assertThat(testStock.getMarketCap()).isEqualTo(3000000000L);
        }

        @Test
        @DisplayName("always updates market field even if null is passed")
        void createOrUpdateStock_alwaysUpdatesMarket() {
            testStock.setMarket("AR");

            when(stockRepository.findBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(stockRepository.save(any(Stock.class))).thenReturn(testStock);

            stockService.createOrUpdateStock(
                    "AAPL", "US", null, null, null, null, null, null, null
            );

            assertThat(testStock.getMarket()).isEqualTo("US");
        }
    }
}