import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { DashboardComponent } from './dashboard.component';
import { Signal } from '../../models/stock.model';

describe('DashboardComponent Helper Methods', () => {
  let component: DashboardComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        FormsModule,
        MatCardModule,
        MatTableModule,
        MatToolbarModule,
        MatIconModule
      ],
      providers: []
    });

    const fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  describe('formatMarketCap', () => {
    it('should return empty string for falsy values', () => {
      expect(component.formatMarketCap(0)).toBe('');
      expect(component.formatMarketCap(null as any)).toBe('');
      expect(component.formatMarketCap(undefined as any)).toBe('');
    });

    it('should format trillions correctly', () => {
      expect(component.formatMarketCap(1e12)).toBe('$1.0T');
      expect(component.formatMarketCap(2.5e12)).toBe('$2.5T');
    });

    it('should format billions correctly', () => {
      expect(component.formatMarketCap(1e9)).toBe('$1.0B');
      expect(component.formatMarketCap(500e9)).toBe('$500.0B');
      expect(component.formatMarketCap(3.7e9)).toBe('$3.7B');
    });

    it('should format millions correctly', () => {
      expect(component.formatMarketCap(1e6)).toBe('$1.0M');
      expect(component.formatMarketCap(250e6)).toBe('$250.0M');
    });

    it('should format smaller numbers with locale string', () => {
      expect(component.formatMarketCap(500000)).toBe('$500.000');
      expect(component.formatMarketCap(999999)).toBe('$999.999');
    });
  });

  describe('getRecommendation', () => {
    it('should return BUY recommendation for BUY signalType', () => {
      const result = component.getRecommendation('BUY');
      expect(result).toContain('COMPRAR');
      expect(result).toContain('✅');
    });

    it('should return SELL recommendation for SELL signalType', () => {
      const result = component.getRecommendation('SELL');
      expect(result).toContain('VENDER');
      expect(result).toContain('🔻');
    });

    it('should return HOLD recommendation for HOLD signalType', () => {
      const result = component.getRecommendation('HOLD');
      expect(result).toContain('MANTENER');
      expect(result).toContain('⏳');
    });

    it('should return HOLD for unknown signalType', () => {
      const result = component.getRecommendation('UNKNOWN');
      expect(result).toContain('MANTENER');
      expect(result).toContain('⏳');
    });
  });

  describe('getTrendIcon', () => {
    it('should return up arrow for ALCISTA', () => {
      expect(component.getTrendIcon('ALCISTA')).toBe('↑');
    });

    it('should return down arrow for BAJISTA', () => {
      expect(component.getTrendIcon('BAJISTA')).toBe('↓');
    });

    it('should return right arrow for other trends', () => {
      expect(component.getTrendIcon('LATERAL')).toBe('→');
      expect(component.getTrendIcon('OTHER')).toBe('→');
    });
  });

  describe('getTrendClass', () => {
    it('should return trend-up for ALCISTA', () => {
      expect(component.getTrendClass('ALCISTA')).toBe('trend-up');
    });

    it('should return trend-down for BAJISTA', () => {
      expect(component.getTrendClass('BAJISTA')).toBe('trend-down');
    });

    it('should return trend-neu for LATERAL', () => {
      expect(component.getTrendClass('LATERAL')).toBe('trend-neu');
    });
  });

  describe('getReasonCategory', () => {
    it('should return trend type for EMA reasons', () => {
      const result = component.getReasonCategory('EMA crossed above');
      expect(result.type).toBe('trend');
      expect(result.label).toBe('Tendencia');
      expect(result.color).toBe('#22c55e');
    });

    it('should return trend type for tendencia reasons', () => {
      const result = component.getReasonCategory('La tendencia es positiva');
      expect(result.type).toBe('trend');
    });

    it('should return RSI type for RSI reasons', () => {
      const result = component.getReasonCategory('RSI is oversold');
      expect(result.type).toBe('rsi');
      expect(result.label).toBe('RSI');
      expect(result.color).toBe('#f59e0b');
    });

    it('should return MACD type for MACD reasons', () => {
      const result = component.getReasonCategory('MACD bullish divergence');
      expect(result.type).toBe('macd');
      expect(result.label).toBe('MACD');
      expect(result.color).toBe('#8b5cf6');
    });

    it('should return Stoch type for stoch reasons', () => {
      const result = component.getReasonCategory('Stochastic overbought');
      expect(result.type).toBe('stoch');
      expect(result.label).toBe('Stoch');
      expect(result.color).toBe('#06b6d4');
    });

    it('should return Others for unknown reasons', () => {
      const result = component.getReasonCategory('Volume spike');
      expect(result.type).toBe('other');
      expect(result.label).toBe('Otros');
      expect(result.color).toBe('#94a3b8');
    });
  });

  describe('getRecommendationTitle', () => {
    it('should return COMPRA title for BUY signal', () => {
      const signal = { signalType: 'BUY' } as Signal;
      expect(component.getRecommendationTitle(signal)).toBe('Señal de COMPRA');
    });

    it('should return VENTA title for SELL signal', () => {
      const signal = { signalType: 'SELL' } as Signal;
      expect(component.getRecommendationTitle(signal)).toBe('Señal de VENTA');
    });

    it('should return Mantener for HOLD signal', () => {
      const signal = { signalType: 'HOLD' } as Signal;
      expect(component.getRecommendationTitle(signal)).toBe('Mantener');
    });
  });

  describe('getRecommendationText', () => {
    it('should return buy text for BUY signal', () => {
      const signal = { signalType: 'BUY' } as Signal;
      const text = component.getRecommendationText(signal);
      expect(text).toContain('compra');
      expect(text).toContain('subir');
    });

    it('should return sell text for SELL signal', () => {
      const signal = { signalType: 'SELL' } as Signal;
      const text = component.getRecommendationText(signal);
      expect(text).toContain('debilidad');
      expect(text).toContain('vender');
    });

    it('should return neutral text for HOLD signal', () => {
      const signal = { signalType: 'HOLD' } as Signal;
      const text = component.getRecommendationText(signal);
      expect(text).toContain('confirmación');
    });
  });

  describe('toggleReasonsExpanded', () => {
    it('should toggle reasonsExpanded from false to true', () => {
      component.reasonsExpanded = false;
      component.toggleReasonsExpanded();
      expect(component.reasonsExpanded).toBe(true);
    });

    it('should toggle reasonsExpanded from true to false', () => {
      component.reasonsExpanded = true;
      component.toggleReasonsExpanded();
      expect(component.reasonsExpanded).toBe(false);
    });
  });
});