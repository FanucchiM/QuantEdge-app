import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Signal, PageResponse, StockHistory } from '../models/stock.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SignalService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getTodaySignals(): Observable<Signal[]> {
    return this.http.get<Signal[]>(`${this.apiUrl}/signals/today`);
  }

  getSignals(page: number = 0, size: number = 15): Observable<PageResponse<Signal>> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());
    
    return this.http.get<PageResponse<Signal>>(`${this.apiUrl}/signals`, { params });
  }

  getSignalHistory(page: number = 0, size: number = 20): Observable<PageResponse<Signal>> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());
    
    return this.http.get<PageResponse<Signal>>(`${this.apiUrl}/signals/history`, { params });
  }

  getStockSignal(symbol: string): Observable<Signal> {
    return this.http.get<Signal>(`${this.apiUrl}/stocks/${symbol}`);
  }

  getStockHistory(symbol: string, days: number = 60): Observable<StockHistory> {
    const params = new HttpParams()
      .set('days', days.toString());
    
    return this.http.get<StockHistory>(`${this.apiUrl}/stocks/${symbol}/history`, { params });
  }

  getStockSeasonality(symbol: string, years: string = '2026,2025,2024'): Observable<any> {
    const params = new HttpParams()
      .set('years', years);
    
    return this.http.get<any>(`${this.apiUrl}/stocks/${symbol}/seasonality`, { params });
  }
}
