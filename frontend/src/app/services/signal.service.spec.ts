import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { SignalService } from './signal.service';
import { Signal, PageResponse } from '../models/stock.model';
import { environment } from '../../environments/environment';

describe('SignalService', () => {
  let service: SignalService;
  let httpMock: HttpTestingController;

  const createMockSignal = (overrides: Partial<Signal> = {}): Signal => ({
    id: 1,
    symbol: 'AAPL',
    companyName: 'Apple',
    market: 'US',
    signalType: 'BUY',
    rsi: 45,
    ema20: 150,
    ema50: 145,
    macd: 0.5,
    atr: 2.3,
    price: 185,
    priceChange24h: 2.5,
    priceChangePercent24h: 1.37,
    trend: 'BULLISH',
    explanation: 'Test signal',
    analyzedAt: '2026-04-28',
    ...overrides
  });

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SignalService]
    });

    service = TestBed.inject(SignalService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('getTodaySignals', () => {
    it('should return an array of signals', () => {
      const mockSignal = createMockSignal();

      service.getTodaySignals().subscribe((signals) => {
        expect(signals).toEqual([mockSignal]);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/signals/today`);
      expect(req.request.method).toBe('GET');
      req.flush([mockSignal]);
    });

    it('should handle empty response', () => {
      service.getTodaySignals().subscribe((signals) => {
        expect(signals).toEqual([]);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/signals/today`);
      req.flush([]);
    });
  });

  describe('getSignals', () => {
    it('should send pagination parameters', () => {
      const mockPageResponse: PageResponse<Signal> = {
        content: [createMockSignal()],
        totalElements: 1,
        totalPages: 1,
        size: 20,
        number: 2,
        last: false,
        first: false
      };

      service.getSignals(2, 20).subscribe((response) => {
        expect(response.totalElements).toBe(1);
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/signals` &&
               request.params.get('page') === '2' &&
               request.params.get('size') === '20';
      });
      expect(req.request.method).toBe('GET');
      req.flush(mockPageResponse);
    });

    it('should use default pagination values when not specified', () => {
      const mockPageResponse: PageResponse<Signal> = {
        content: [],
        totalElements: 0,
        totalPages: 0,
        size: 15,
        number: 0,
        last: true,
        first: true
      };

      service.getSignals().subscribe((response) => {
        expect(response.size).toBe(15);
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/signals` &&
               request.params.get('page') === '0' &&
               request.params.get('size') === '15';
      });
      req.flush(mockPageResponse);
    });
  });

  describe('getSignalHistory', () => {
    it('should call signals/history endpoint with pagination', () => {
      const mockPageResponse: PageResponse<Signal> = {
        content: [],
        totalElements: 0,
        totalPages: 0,
        size: 50,
        number: 1,
        last: true,
        first: false
      };

      service.getSignalHistory(1, 50).subscribe((response) => {
        expect(response.size).toBe(50);
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/signals/history` &&
               request.params.get('page') === '1' &&
               request.params.get('size') === '50';
      });
      req.flush(mockPageResponse);
    });
  });

  describe('getStockSignal', () => {
    it('should fetch signal for specific symbol', () => {
      const mockSignal = createMockSignal({ symbol: 'MSFT', companyName: 'Microsoft' });

      service.getStockSignal('MSFT').subscribe((signal) => {
        expect(signal.symbol).toBe('MSFT');
        expect(signal.companyName).toBe('Microsoft');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/stocks/MSFT`);
      expect(req.request.method).toBe('GET');
      req.flush(mockSignal);
    });

    it('should handle 404 for unknown symbol', () => {
      service.getStockSignal('UNKNOWN').subscribe({
        error: (error) => {
          expect(error.status).toBe(404);
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/stocks/UNKNOWN`);
      req.flush(null, { status: 404, statusText: 'Not Found' });
    });
  });

  describe('getStockHistory', () => {
    it('should include days parameter in request', () => {
      const mockHistory = {
        symbol: 'AAPL',
        companyName: 'Apple',
        market: 'US',
        chartData: { dates: [], price: [], ema20: [], ema50: [], rsi: [] }
      };

      service.getStockHistory('AAPL', 90).subscribe((response) => {
        expect(response.symbol).toBe('AAPL');
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/stocks/AAPL/history` &&
               request.params.get('days') === '90';
      });
      req.flush(mockHistory);
    });

    it('should use default days value of 60', () => {
      const mockHistory = {
        symbol: 'AAPL',
        chartData: { dates: [], price: [], ema20: [], ema50: [], rsi: [] }
      };

      service.getStockHistory('AAPL').subscribe((response) => {
        expect(response.symbol).toBe('AAPL');
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/stocks/AAPL/history` &&
               request.params.get('days') === '60';
      });
      req.flush(mockHistory);
    });
  });

  describe('getStockSeasonality', () => {
    it('should include years parameter in request', () => {
      const mockSeasonality = {
        years: ['2026', '2025'],
        monthlyAvg: [1.1, 2.2, 3.3]
      };

      service.getStockSeasonality('AAPL', '2026').subscribe((response) => {
        expect(response.years).toEqual(['2026', '2025']);
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/stocks/AAPL/seasonality` &&
               request.params.get('years') === '2026,2025';
      });
      req.flush(mockSeasonality);
    });

    it('should use default years parameter', () => {
      const mockSeasonality = {
        years: ['2026', '2025', '2024'],
        monthlyAvg: []
      };

      service.getStockSeasonality('AAPL').subscribe((response) => {
        expect(response.years.length).toBe(2);
      });

      const req = httpMock.expectOne((request) => {
        return request.url === `${environment.apiUrl}/stocks/AAPL/seasonality` &&
               request.params.get('years') === '2026,2025';
      });
      req.flush(mockSeasonality);
    });
  });
});