package com.stockanalyzer.controller;

import com.stockanalyzer.dto.SignalDTO;
import com.stockanalyzer.dto.SignalRequestDTO;
import com.stockanalyzer.service.ISignalService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@Validated
public class SignalController {
    private final ISignalService signalService;
    
    public SignalController(ISignalService signalService) {
        this.signalService = signalService;
    }
    
    @GetMapping("/signals/today")
    public ResponseEntity<List<SignalDTO>> getTodaySignals() {
        List<SignalDTO> signals = signalService.getTodaySignals();
        return ResponseEntity.ok(signals);
    }
    
    @GetMapping("/signals")
    public ResponseEntity<Page<SignalDTO>> getSignals(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "100") @Min(1) @Max(500) int size) {
        Sort sort = Sort.by(Sort.Direction.ASC, "stock.market").and(Sort.by(Sort.Direction.DESC, "analyzedAt"));
        PageRequest pageable = PageRequest.of(page, size, sort);
        Page<SignalDTO> signals = signalService.getTodaySignalsPaginated(pageable);
        return ResponseEntity.ok(signals);
    }
    
    @GetMapping("/signals/history")
    public ResponseEntity<Page<SignalDTO>> getSignalHistory(
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        Sort sort = Sort.by(Sort.Direction.ASC, "stock.market").and(Sort.by(Sort.Direction.DESC, "analyzedAt"));
        PageRequest pageable = PageRequest.of(page, size, sort);
        Page<SignalDTO> signals = signalService.getSignalHistory(pageable);
        return ResponseEntity.ok(signals);
    }
    
    @GetMapping("/signals/{symbol}")
    public ResponseEntity<SignalDTO> getStockSignal(@PathVariable String symbol) {
        SignalDTO signal = signalService.getLatestSignalBySymbol(symbol);
        if (signal == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(signal);
    }
    
    @PostMapping("/signals/batch")
    public ResponseEntity<?> receiveSignals(@Valid @RequestBody List<SignalRequestDTO> signals) {
        try {
            List<SignalDTO> saved = signalService.saveSignals(signals);
            return ResponseEntity.ok(Map.of("saved", saved.size(), "signals", saved));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        }
    }
    
    @PostMapping("/signals")
    public ResponseEntity<SignalDTO> receiveSignal(@Valid @RequestBody SignalRequestDTO signal) {
        SignalDTO saved = signalService.saveSignal(signal);
        return ResponseEntity.ok(saved);
    }
    
    @DeleteMapping("/signals/today")
    public ResponseEntity<?> deleteTodaySignals() {
        int deleted = signalService.deleteTodaySignals();
        return ResponseEntity.ok(Map.of("deleted", deleted));
    }
}
