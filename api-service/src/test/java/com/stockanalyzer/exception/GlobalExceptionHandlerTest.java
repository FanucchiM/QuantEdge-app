package com.stockanalyzer.exception;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stockanalyzer.controller.SignalController;
import com.stockanalyzer.dto.SignalRequestDTO;
import com.stockanalyzer.service.ISignalService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(SignalController.class)
class GlobalExceptionHandlerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ISignalService signalService;

    @Nested
    @DisplayName("handleNotFound")
    class HandleNotFoundTests {

        @Test
        @DisplayName("returns 404 when signal not found")
        void getSignal_notFound_returns404() throws Exception {
            when(signalService.getLatestSignalBySymbol("UNKNOWN")).thenReturn(null);

            mockMvc.perform(get("/api/signals/UNKNOWN"))
                    .andExpect(status().isNotFound());
        }
    }

    @Nested
    @DisplayName("handleValidationErrors")
    class HandleValidationErrorsTests {

        @Test
        @DisplayName("returns 400 when symbol is blank")
        void receiveSignal_blankSymbol_returns400() throws Exception {
            SignalRequestDTO invalidRequest = new SignalRequestDTO();
            invalidRequest.setSymbol("");
            invalidRequest.setMarket("US");
            invalidRequest.setSignalType("BUY");

            mockMvc.perform(post("/api/signals")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(invalidRequest)))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error").value("Validation Failed"));
        }

        @Test
        @DisplayName("returns 400 when market is invalid")
        void receiveSignal_invalidMarket_returns400() throws Exception {
            SignalRequestDTO invalidRequest = new SignalRequestDTO();
            invalidRequest.setSymbol("AAPL");
            invalidRequest.setMarket("INVALID");
            invalidRequest.setSignalType("BUY");

            mockMvc.perform(post("/api/signals")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(invalidRequest)))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error").value("Validation Failed"));
        }

        @Test
        @DisplayName("returns 400 when signalType is invalid")
        void receiveSignal_invalidSignalType_returns400() throws Exception {
            SignalRequestDTO invalidRequest = new SignalRequestDTO();
            invalidRequest.setSymbol("AAPL");
            invalidRequest.setMarket("US");
            invalidRequest.setSignalType("INVALID_TYPE");

            mockMvc.perform(post("/api/signals")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(invalidRequest)))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error").value("Validation Failed"));
        }
    }

    @Nested
    @DisplayName("handleGenericException")
    class HandleGenericExceptionTests {

        @Test
        @DisplayName("returns 500 when service throws unexpected exception")
        void serviceThrowsUnexpectedException_returns500() throws Exception {
            when(signalService.getTodaySignals()).thenThrow(new RuntimeException("Database connection lost"));

            mockMvc.perform(get("/api/signals/today"))
                    .andExpect(status().isInternalServerError())
                    .andExpect(jsonPath("$.error").value("Internal Server Error"))
                    .andExpect(jsonPath("$.message").value("An unexpected error occurred"));
        }
    }
}