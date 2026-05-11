package com.stockanalyzer.controller;

import com.stockanalyzer.model.Stock;
import com.stockanalyzer.service.IStockService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(StockController.class)
class StockControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private IStockService stockService;

    @MockBean
    private org.springframework.web.client.RestTemplate restTemplate;

    private Stock testStock;

    @BeforeEach
    void setUp() {
        testStock = new Stock();
        testStock.setId(1L);
        testStock.setSymbol("AAPL");
        testStock.setMarket("US");
        testStock.setName("Apple Inc.");
        testStock.setSector("Technology");
        testStock.setIndustry("Consumer Electronics");
        testStock.setExchange("NASDAQ");
        testStock.setCountry("USA");
        testStock.setLogoUrl("https://logo.url");
        testStock.setMarketCap(3000000000L);
        testStock.setCreatedAt(LocalDateTime.now());
        testStock.setUpdatedAt(LocalDateTime.now());
    }

    @Nested
    @DisplayName("GET /api/stocks")
    class GetAllStocksTests {

        @Test
        @DisplayName("returns all stocks")
        void getAllStocks_returnsAllStocks() throws Exception {
            when(stockService.getAllStocks()).thenReturn(List.of(testStock));

            mockMvc.perform(get("/api/stocks"))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$", hasSize(1)))
                    .andExpect(jsonPath("$[0].symbol", is("AAPL")));
        }

        @Test
        @DisplayName("returns empty list when no stocks")
        void getAllStocks_empty_returnsEmptyList() throws Exception {
            when(stockService.getAllStocks()).thenReturn(List.of());

            mockMvc.perform(get("/api/stocks"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$", hasSize(0)));
        }
    }

    @Nested
    @DisplayName("GET /api/stocks/{symbol}")
    class GetStockTests {

        @Test
        @DisplayName("returns stock when found")
        void getStock_found_returnsStock() throws Exception {
            when(stockService.getStockBySymbol("AAPL")).thenReturn(Optional.of(testStock));

            mockMvc.perform(get("/api/stocks/AAPL"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.symbol", is("AAPL")))
                    .andExpect(jsonPath("$.name", is("Apple Inc.")));
        }

        @Test
        @DisplayName("returns 404 when not found")
        void getStock_notFound_returns404() throws Exception {
            when(stockService.getStockBySymbol("UNKNOWN")).thenReturn(Optional.empty());

            mockMvc.perform(get("/api/stocks/UNKNOWN"))
                    .andExpect(status().isNotFound());
        }
    }

    @Nested
    @DisplayName("GET /api/stocks/{symbol}/history")
    class GetStockHistoryTests {

        @Test
        @DisplayName("returns history data from analytics service")
        void getStockHistory_success_returnsData() throws Exception {
            Map<String, Object> historyData = Map.of(
                    "symbol", "AAPL",
                    "prices", List.of(150.0, 155.0, 160.0),
                    "dates", List.of("2026-04-25", "2026-04-26", "2026-04-27")
            );

            when(restTemplate.exchange(
                    anyString(),
                    eq(HttpMethod.GET),
                    isNull(),
                    eq(Map.class)
            )).thenReturn(ResponseEntity.ok(historyData));

            mockMvc.perform(get("/api/stocks/AAPL/history"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.symbol", is("AAPL")))
                    .andExpect(jsonPath("$.prices", hasSize(3)));
        }

        @Test
        @DisplayName("returns 503 when analytics service is unavailable")
        void getStockHistory_serviceUnavailable_returns503() throws Exception {
            when(restTemplate.exchange(
                    anyString(),
                    eq(HttpMethod.GET),
                    isNull(),
                    eq(Map.class)
            )).thenThrow(new org.springframework.web.client.RestClientException("Connection refused"));

            mockMvc.perform(get("/api/stocks/AAPL/history"))
                    .andExpect(status().isServiceUnavailable())
                    .andExpect(jsonPath("$.error").exists());
        }

        @Test
        @DisplayName("returns history with custom days parameter")
        void getStockHistory_customDays_returnsData() throws Exception {
            Map<String, Object> historyData = Map.of(
                    "symbol", "AAPL",
                    "days", 30
            );

            when(restTemplate.exchange(
                    contains("days=30"),
                    eq(HttpMethod.GET),
                    isNull(),
                    eq(Map.class)
            )).thenReturn(ResponseEntity.ok(historyData));

            mockMvc.perform(get("/api/stocks/AAPL/history")
                            .param("days", "30"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.days", is(30)));
        }
    }

    @Nested
    @DisplayName("GET /api/stocks/{symbol}/seasonality")
    class GetStockSeasonalityTests {

        @Test
        @DisplayName("returns seasonality data from analytics service")
        void getStockSeasonality_success_returnsData() throws Exception {
            Map<String, Object> seasonalityData = Map.of(
                    "symbol", "AAPL",
                    "yearly", List.of(1.1, 1.2, 0.9, 1.0, 1.3)
            );

            when(restTemplate.exchange(
                    anyString(),
                    eq(HttpMethod.GET),
                    isNull(),
                    eq(Object.class)
            )).thenReturn(ResponseEntity.ok(seasonalityData));

            mockMvc.perform(get("/api/stocks/AAPL/seasonality"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.symbol", is("AAPL")))
                    .andExpect(jsonPath("$.yearly", hasSize(5)));
        }

        @Test
        @DisplayName("returns 503 when analytics service is unavailable")
        void getStockSeasonality_serviceUnavailable_returns503() throws Exception {
            when(restTemplate.exchange(
                    anyString(),
                    eq(HttpMethod.GET),
                    isNull(),
                    eq(Object.class)
            )).thenThrow(new org.springframework.web.client.RestClientException("Connection refused"));

            mockMvc.perform(get("/api/stocks/AAPL/seasonality"))
                    .andExpect(status().isServiceUnavailable())
                    .andExpect(jsonPath("$.error").exists());
        }

        @Test
        @DisplayName("returns seasonality with custom years parameter")
        void getStockSeasonality_customYears_returnsData() throws Exception {
            Map<String, Object> seasonalityData = Map.of(
                    "symbol", "AAPL",
                    "years", "2026,2025"
            );

            when(restTemplate.exchange(
                    contains("years=2026,2025"),
                    eq(HttpMethod.GET),
                    isNull(),
                    eq(Object.class)
            )).thenReturn(ResponseEntity.ok(seasonalityData));

            mockMvc.perform(get("/api/stocks/AAPL/seasonality")
                            .param("years", "2026,2025"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.years", is("2026,2025")));
        }
    }
}