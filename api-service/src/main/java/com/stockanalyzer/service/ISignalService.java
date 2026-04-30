package com.stockanalyzer.service;

import com.stockanalyzer.dto.SignalDTO;
import com.stockanalyzer.dto.SignalRequestDTO;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;

public interface ISignalService {
    
    List<SignalDTO> getTodaySignals();
    
    Page<SignalDTO> getTodaySignalsPaginated(Pageable pageable);
    
    Page<SignalDTO> getSignalHistory(Pageable pageable);
    
    SignalDTO getLatestSignalBySymbol(String symbol);
    
    SignalDTO saveSignal(SignalRequestDTO requestDTO);
    
    List<SignalDTO> saveSignals(List<SignalRequestDTO> requests);
    
    int deleteTodaySignals();
}