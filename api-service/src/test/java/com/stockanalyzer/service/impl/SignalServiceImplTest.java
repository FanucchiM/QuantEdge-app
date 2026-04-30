package com.stockanalyzer.service.impl;

import com.stockanalyzer.dto.SignalDTO;
import com.stockanalyzer.dto.SignalRequestDTO;
import com.stockanalyzer.model.Signal;
import com.stockanalyzer.model.Stock;
import com.stockanalyzer.repository.SignalRepository;
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
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class SignalServiceImplTest {

    @Mock
    private SignalRepository signalRepository;

    @Mock
    private IStockService stockService;

    @InjectMocks
    private SignalServiceImpl signalService;

    private Stock testStock;
    private Signal testSignal;
    private SignalRequestDTO testRequestDTO;

    @BeforeEach
    void setUp() {
        testStock = new Stock();
        testStock.setId(1L);
        testStock.setSymbol("AAPL");
        testStock.setMarket("US");
        testStock.setName("Apple Inc.");

        testSignal = new Signal();
        testSignal.setId(1L);
        testSignal.setStock(testStock);
        testSignal.setSignalType("BUY");
        testSignal.setRsi(45.0);
        testSignal.setTrend("BULLISH");
        testSignal.setAnalyzedAt(LocalDateTime.now());

        testRequestDTO = new SignalRequestDTO();
        testRequestDTO.setSymbol("AAPL");
        testRequestDTO.setMarket("US");
        testRequestDTO.setSignalType("BUY");
        testRequestDTO.setTrend("BULLISH");
        testRequestDTO.setRsi(45.0);
        testRequestDTO.setAnalyzedAt(LocalDateTime.now());
    }

    @Nested
    @DisplayName("getTodaySignals")
    class GetTodaySignalsTests {

        @Test
        @DisplayName("returns empty list when no signals exist")
        void getTodaySignals_empty_returnsEmptyList() {
            when(signalRepository.findByAnalyzedAtAfterWithStock(any(LocalDateTime.class)))
                    .thenReturn(new ArrayList<>());

            List<SignalDTO> result = signalService.getTodaySignals();

            assertThat(result).isEmpty();
            verify(signalRepository).findByAnalyzedAtAfterWithStock(any(LocalDateTime.class));
        }

        @Test
        @DisplayName("returns signals sorted by market order then symbol")
        void getTodaySignals_withSignals_returnsSortedSignals() {
            Stock arStock = new Stock();
            arStock.setSymbol("YPF");
            arStock.setMarket("AR");

            Stock usStock = new Stock();
            usStock.setSymbol("AAPL");
            usStock.setMarket("US");

            Signal arSignal = new Signal();
            arSignal.setStock(arStock);
            arSignal.setAnalyzedAt(LocalDateTime.now());

            Signal usSignal = new Signal();
            usSignal.setStock(usStock);
            usSignal.setAnalyzedAt(LocalDateTime.now());

            when(signalRepository.findByAnalyzedAtAfterWithStock(any(LocalDateTime.class)))
                    .thenReturn(new ArrayList<>(List.of(usSignal, arSignal)));

            List<SignalDTO> result = signalService.getTodaySignals();

            assertThat(result).hasSize(2);
            assertThat(result.get(0).getSymbol()).isEqualTo("YPF");
            assertThat(result.get(1).getSymbol()).isEqualTo("AAPL");
        }
    }

    @Nested
    @DisplayName("saveSignal")
    class SaveSignalTests {

        @Test
        @DisplayName("creates signal with all fields")
        void saveSignal_basic_createsSignal() {
            when(stockService.createOrUpdateStock(
                    any(), any(), any(), any(), any(),
                    any(), any(), any(), any()))
                    .thenReturn(testStock);
            when(signalRepository.save(any(Signal.class))).thenReturn(testSignal);

            SignalDTO result = signalService.saveSignal(testRequestDTO);

            assertThat(result).isNotNull();
            assertThat(result.getSymbol()).isEqualTo("AAPL");
            assertThat(result.getSignalType()).isEqualTo("BUY");

            verify(stockService).createOrUpdateStock(
                    any(), any(), any(), any(), any(),
                    any(), any(), any(), any());
            verify(signalRepository).save(any(Signal.class));
        }

        @Test
        @DisplayName("maps all fields correctly from request to signal")
        void saveSignal_mapsAllFields() {
            testRequestDTO.setRsi(65.0);
            testRequestDTO.setEma20(150.5);
            testRequestDTO.setEma50(145.2);
            testRequestDTO.setMacd(0.5);
            testRequestDTO.setAtr(2.3);
            testRequestDTO.setPrice(185.0);
            testRequestDTO.setPriceChange24h(2.5);
            testRequestDTO.setPriceChangePercent24h(1.37);
            testRequestDTO.setVolumeRelative(1.2);
            testRequestDTO.setTrend("BULLISH");
            testRequestDTO.setExplanation("Test explanation");
            testRequestDTO.setSummary("Test summary");
            testRequestDTO.setReasons("Reason 1, Reason 2");
            testRequestDTO.setCompanyName("Apple Inc.");
            testRequestDTO.setSector("Technology");
            testRequestDTO.setIndustry("Consumer Electronics");
            testRequestDTO.setExchange("NASDAQ");
            testRequestDTO.setCountry("USA");
            testRequestDTO.setLogoUrl("https://logo.url");
            testRequestDTO.setMarketCap(3000000000L);

            when(stockService.createOrUpdateStock(
                    any(), any(), any(), any(), any(),
                    any(), any(), any(), any()))
                    .thenReturn(testStock);
            when(signalRepository.save(any(Signal.class))).thenAnswer(invocation -> {
                Signal saved = invocation.getArgument(0);
                saved.setId(1L);
                return saved;
            });

            signalService.saveSignal(testRequestDTO);

            ArgumentCaptor<Signal> signalCaptor = ArgumentCaptor.forClass(Signal.class);
            verify(signalRepository).save(signalCaptor.capture());

            Signal savedSignal = signalCaptor.getValue();
            assertThat(savedSignal.getRsi()).isEqualTo(65.0);
            assertThat(savedSignal.getEma20()).isEqualTo(150.5);
            assertThat(savedSignal.getEma50()).isEqualTo(145.2);
            assertThat(savedSignal.getMacd()).isEqualTo(0.5);
            assertThat(savedSignal.getAtr()).isEqualTo(2.3);
            assertThat(savedSignal.getPrice()).isEqualTo(185.0);
            assertThat(savedSignal.getPriceChange24h()).isEqualTo(2.5);
            assertThat(savedSignal.getPriceChangePercent24h()).isEqualTo(1.37);
            assertThat(savedSignal.getVolumeRelative()).isEqualTo(1.2);
            assertThat(savedSignal.getTrend()).isEqualTo("BULLISH");
            assertThat(savedSignal.getExplanation()).isEqualTo("Test explanation");
            assertThat(savedSignal.getSummary()).isEqualTo("Test summary");
            assertThat(savedSignal.getReasons()).isEqualTo("Reason 1, Reason 2");
        }
    }

    @Nested
    @DisplayName("saveSignals batch operations")
    class SaveSignalsBatchTests {

        @Test
        @DisplayName("deletes existing signals before saving new batch")
        void saveSignals_deletesExistingBeforeSaving() {
            when(stockService.getStockBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(stockService.createOrUpdateStock(
                    any(), any(), any(), any(), any(),
                    any(), any(), any(), any()))
                    .thenReturn(testStock);
            when(signalRepository.save(any(Signal.class))).thenReturn(testSignal);

            signalService.saveSignals(List.of(testRequestDTO));

            verify(signalRepository).deleteByStock(testStock);
            verify(signalRepository).save(any(Signal.class));
        }

        @Test
        @DisplayName("TDD test: rollback on failure exposes partial batch save bug")
        void saveSignals_rollbackOnFailure_exposesBug() {
            Stock msftStock = new Stock();
            msftStock.setId(2L);
            msftStock.setSymbol("MSFT");
            msftStock.setMarket("US");

            when(stockService.getStockBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(stockService.getStockBySymbol("MSFT")).thenReturn(Optional.of(msftStock));
            when(stockService.createOrUpdateStock(
                    any(), any(), any(), any(), any(),
                    any(), any(), any(), any()))
                    .thenReturn(testStock);
            when(signalRepository.save(any(Signal.class)))
                    .thenReturn(testSignal)
                    .thenThrow(new RuntimeException("DB error on signal 2"));

            SignalRequestDTO request2 = new SignalRequestDTO();
            request2.setSymbol("MSFT");
            request2.setMarket("US");
            request2.setSignalType("SELL");
            request2.setTrend("BEARISH");
            request2.setAnalyzedAt(LocalDateTime.now());

            assertThatThrownBy(() -> signalService.saveSignals(List.of(testRequestDTO, request2)))
                    .isInstanceOf(RuntimeException.class)
                    .hasMessage("DB error on signal 2");

            verify(signalRepository, times(2)).deleteByStock(any(Stock.class));
            verify(signalRepository, times(2)).save(any(Signal.class));
        }

        @Test
        @DisplayName("processes multiple signals in batch")
        void saveSignals_multipleSignals_processesAll() {
            Stock msftStock = new Stock();
            msftStock.setId(2L);
            msftStock.setSymbol("MSFT");
            msftStock.setMarket("US");

            when(stockService.getStockBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(stockService.getStockBySymbol("MSFT")).thenReturn(Optional.of(msftStock));
            when(stockService.createOrUpdateStock(
                    any(), any(), any(), any(), any(),
                    any(), any(), any(), any()))
                    .thenReturn(testStock);
            when(signalRepository.save(any(Signal.class))).thenReturn(testSignal);

            SignalRequestDTO request2 = new SignalRequestDTO();
            request2.setSymbol("MSFT");
            request2.setMarket("US");
            request2.setSignalType("SELL");
            request2.setTrend("BEARISH");
            request2.setAnalyzedAt(LocalDateTime.now());

            List<SignalDTO> results = signalService.saveSignals(List.of(testRequestDTO, request2));

            assertThat(results).hasSize(2);
            verify(signalRepository, times(2)).deleteByStock(any(Stock.class));
            verify(signalRepository, times(2)).save(any(Signal.class));
        }
    }

    @Nested
    @DisplayName("getTodaySignalsPaginated")
    class GetTodaySignalsPaginatedTests {

        @Test
        @DisplayName("returns paginated signals")
        void getTodaySignalsPaginated_returnsPage() {
            Pageable pageable = PageRequest.of(0, 10);
            Page<Signal> signalPage = new PageImpl<>(List.of(testSignal));

            when(signalRepository.findByAnalyzedAtAfter(any(LocalDateTime.class), eq(pageable)))
                    .thenReturn(signalPage);

            Page<SignalDTO> result = signalService.getTodaySignalsPaginated(pageable);

            assertThat(result.getContent()).hasSize(1);
            assertThat(result.getContent().get(0).getSymbol()).isEqualTo("AAPL");
        }
    }

    @Nested
    @DisplayName("getSignalHistory")
    class GetSignalHistoryTests {

        @Test
        @DisplayName("returns signal history with default days")
        void getSignalHistory_returnsSignals() {
            Pageable pageable = PageRequest.of(0, 10);
            Page<Signal> signalPage = new PageImpl<>(List.of(testSignal));

            when(signalRepository.findByAnalyzedAtAfter(any(LocalDateTime.class), eq(pageable)))
                    .thenReturn(signalPage);

            Page<SignalDTO> result = signalService.getSignalHistory(pageable);

            assertThat(result.getContent()).hasSize(1);
        }
    }

    @Nested
    @DisplayName("getLatestSignalBySymbol")
    class GetLatestSignalBySymbolTests {

        @Test
        @DisplayName("returns null when stock not found")
        void getLatestSignalBySymbol_stockNotFound_returnsNull() {
            when(stockService.getStockBySymbol("UNKNOWN")).thenReturn(Optional.empty());

            SignalDTO result = signalService.getLatestSignalBySymbol("UNKNOWN");

            assertThat(result).isNull();
        }

        @Test
        @DisplayName("returns latest signal for existing stock")
        void getLatestSignalBySymbol_stockExists_returnsSignal() {
            when(stockService.getStockBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(signalRepository.findTopByStockOrderByAnalyzedAtDesc(testStock))
                    .thenReturn(Optional.of(testSignal));

            SignalDTO result = signalService.getLatestSignalBySymbol("AAPL");

            assertThat(result).isNotNull();
            assertThat(result.getSymbol()).isEqualTo("AAPL");
        }

        @Test
        @DisplayName("returns null when no signal exists for stock")
        void getLatestSignalBySymbol_noSignal_returnsNull() {
            when(stockService.getStockBySymbol("AAPL")).thenReturn(Optional.of(testStock));
            when(signalRepository.findTopByStockOrderByAnalyzedAtDesc(testStock))
                    .thenReturn(Optional.empty());

            SignalDTO result = signalService.getLatestSignalBySymbol("AAPL");

            assertThat(result).isNull();
        }
    }

    @Nested
    @DisplayName("deleteTodaySignals")
    class DeleteTodaySignalsTests {

        @Test
        @DisplayName("deletes today signals and returns count")
        void deleteTodaySignals_deletesAndReturnsCount() {
            when(signalRepository.deleteByAnalyzedAtAfter(any(LocalDateTime.class))).thenReturn(5);

            int result = signalService.deleteTodaySignals();

            assertThat(result).isEqualTo(5);
            verify(signalRepository).deleteByAnalyzedAtAfter(any(LocalDateTime.class));
        }
    }
}