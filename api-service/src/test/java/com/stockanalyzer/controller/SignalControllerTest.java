package com.stockanalyzer.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stockanalyzer.dto.SignalDTO;
import com.stockanalyzer.dto.SignalRequestDTO;
import com.stockanalyzer.service.ISignalService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(SignalController.class)
class SignalControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ISignalService signalService;

    private SignalDTO testSignalDTO;
    private SignalRequestDTO testSignalRequestDTO;

    @BeforeEach
    void setUp() {
        testSignalDTO = new SignalDTO(
                1L, "AAPL", "US", "BUY", 45.0,
                150.5, 145.2, 0.5, 2.3, 185.0,
                2.5, 1.37, 1.2, "BULLISH",
                "Test explanation", "Test summary", "Reason 1, Reason 2",
                "Apple Inc.", "Technology", "Consumer Electronics",
                "NASDAQ", "USA", "https://logo.url", 3000000000L,
                LocalDateTime.now()
        );

        testSignalRequestDTO = new SignalRequestDTO();
        testSignalRequestDTO.setSymbol("AAPL");
        testSignalRequestDTO.setMarket("US");
        testSignalRequestDTO.setSignalType("BUY");
        testSignalRequestDTO.setTrend("BULLISH");
        testSignalRequestDTO.setRsi(45.0);
        testSignalRequestDTO.setAnalyzedAt(LocalDateTime.now());
    }

    @Nested
    @DisplayName("GET /api/signals/today")
    class GetTodaySignalsTests {

        @Test
        @DisplayName("returns list of signals")
        void getTodaySignals_returnsSignals() throws Exception {
            when(signalService.getTodaySignals()).thenReturn(List.of(testSignalDTO));

            mockMvc.perform(get("/api/signals/today"))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$", hasSize(1)))
                    .andExpect(jsonPath("$[0].symbol", is("AAPL")))
                    .andExpect(jsonPath("$[0].signalType", is("BUY")));
        }

        @Test
        @DisplayName("returns empty list when no signals")
        void getTodaySignals_empty_returnsEmptyList() throws Exception {
            when(signalService.getTodaySignals()).thenReturn(List.of());

            mockMvc.perform(get("/api/signals/today"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$", hasSize(0)));
        }
    }

    @Nested
    @DisplayName("GET /api/signals/{symbol}")
    class GetStockSignalTests {

        @Test
        @DisplayName("returns signal when found")
        void getStockSignal_found_returnsSignal() throws Exception {
            when(signalService.getLatestSignalBySymbol("AAPL")).thenReturn(testSignalDTO);

            mockMvc.perform(get("/api/signals/AAPL"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.symbol", is("AAPL")));
        }

        @Test
        @DisplayName("returns 404 when not found")
        void getStockSignal_notFound_returns404() throws Exception {
            when(signalService.getLatestSignalBySymbol("UNKNOWN")).thenReturn(null);

            mockMvc.perform(get("/api/signals/UNKNOWN"))
                    .andExpect(status().isNotFound());
        }
    }

    @Nested
    @DisplayName("POST /api/signals")
    class ReceiveSignalTests {

        @Test
        @DisplayName("saves signal and returns it")
        void receiveSignal_valid_returnsSavedSignal() throws Exception {
            when(signalService.saveSignal(any(SignalRequestDTO.class))).thenReturn(testSignalDTO);

            mockMvc.perform(post("/api/signals")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(testSignalRequestDTO)))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.symbol", is("AAPL")));
        }
    }

    @Nested
    @DisplayName("POST /api/signals/batch")
    class ReceiveSignalsBatchTests {

        @Test
        @DisplayName("saves batch and returns count")
        void receiveSignals_batch_returnsSavedCount() throws Exception {
            when(signalService.saveSignals(any())).thenReturn(List.of(testSignalDTO));

            mockMvc.perform(post("/api/signals/batch")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(List.of(testSignalRequestDTO))))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.saved", is(1)))
                    .andExpect(jsonPath("$.signals", hasSize(1)));
        }

        @Test
        @DisplayName("returns 400 on service exception")
        void receiveSignals_batchServiceException_returns400() throws Exception {
            when(signalService.saveSignals(any())).thenThrow(new RuntimeException("Batch save failed"));

            mockMvc.perform(post("/api/signals/batch")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(List.of(testSignalRequestDTO))))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error", is("Batch save failed")));
        }
    }

    @Nested
    @DisplayName("DELETE /api/signals/today")
    class DeleteTodaySignalsTests {

        @Test
        @DisplayName("deletes today signals and returns count")
        void deleteTodaySignals_returnsDeletedCount() throws Exception {
            when(signalService.deleteTodaySignals()).thenReturn(5);

            mockMvc.perform(delete("/api/signals/today"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.deleted", is(5)));
        }
    }
}