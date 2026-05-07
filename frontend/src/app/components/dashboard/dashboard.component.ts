import { Component, OnInit, OnDestroy, HostListener, ElementRef, ViewChild, AfterViewInit, DestroyRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { SignalService } from '../../services/signal.service';
import { Signal, PageResponse, StockHistory } from '../../models/stock.model';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

export type SortColumn = 'companyName' | 'signalType' | 'market' | null;

export interface SortConfig {
  column: 'companyName' | 'signalType' | 'market';
  direction: 'asc' | 'desc';
}
export type SortDirection = 'asc' | 'desc' | null;

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatTableModule,
    MatToolbarModule,
    MatIconModule
  ],
  template: `
    <div class="dashboard">
      <!-- Modal -->
      <div class="modal-overlay" *ngIf="selectedSignal" (click)="closeModal()"
           role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div class="modal-content modal-large" (click)="$event.stopPropagation()" role="document">
          <!-- Header con Logo -->
          <div class="modal-header">
            <div class="modal-company-info">
              <div class="company-logo-container" *ngIf="(selectedSignal?.logoUrl || stockHistory?.logoUrl) && (selectedSignal?.logoUrl || stockHistory?.logoUrl) !== ''">
                <img [src]="selectedSignal?.logoUrl || stockHistory?.logoUrl" alt="Logo" class="company-logo" (error)="onLogoError($event)" (load)="onLogoLoad()" #logoImg>
                <span *ngIf="!logoLoaded" class="company-logo-fallback">📊</span>
              </div>
              <div class="company-logo-container" *ngIf="!selectedSignal?.logoUrl && (!stockHistory?.logoUrl || stockHistory?.logoUrl === '')">
                <span class="company-logo-fallback">📊</span>
              </div>
              <div class="modal-title-section">
                <h2 id="modal-title">{{ selectedSignal.companyName || selectedSignal.symbol }}</h2>
                <span class="modal-symbol">{{ selectedSignal.symbol }} · {{ selectedSignal.market }}</span>
              </div>
            </div>
            <button class="modal-close-btn" (click)="closeModal()">✕</button>
          </div>

          <!-- Metadata badges -->
          <div class="modal-metadata" *ngIf="stockHistory">
            <span class="meta-badge" *ngIf="stockHistory.sector">{{ stockHistory.sector }}</span>
            <span class="meta-badge" *ngIf="stockHistory.industry">{{ stockHistory.industry }}</span>
            <span class="meta-badge" *ngIf="stockHistory.exchange">{{ stockHistory.exchange }}</span>
            <span class="meta-badge" *ngIf="stockHistory.country">{{ stockHistory.country }}</span>
            <span class="meta-badge market-cap" *ngIf="stockHistory.marketCap">{{ formatMarketCap(stockHistory.marketCap) }}</span>
          </div>

          <!-- Signal -->
          <div class="modal-signal-pill" [class]="selectedSignal.signalType.toLowerCase()">
            {{ selectedSignal.signalType }}
          </div>

          <!-- Recomendación -->
          <div class="recommendation" [class]="selectedSignal.signalType.toLowerCase()">
            {{ getRecommendation(selectedSignal.signalType) }}
          </div>

          <!-- Análisis en lenguaje natural (arriba del gráfico) -->
          <div class="modal-section" *ngIf="selectedSignal.summary">
            <h3>Analysis</h3>
            <p class="analysis-text">{{ selectedSignal.summary }}</p>
          </div>

          <!-- Gráfico de Estacionalidad -->
          <div class="chart-section">
            <div class="chart-header">
              <h3>Historical Performance</h3>
            </div>
            
            <div *ngIf="loadingHistory || loadingSeasonality" class="chart-loading">
              <div class="spinner-small"></div>
              <span>Loading data...</span>
            </div>
            
            <div class="chart-container" *ngIf="!loadingSeasonality && seasonalityData">
              <canvas #seasonalityChart></canvas>
            </div>
            
            <div class="chart-container" *ngIf="!loadingSeasonality && !seasonalityData">
              <div class="chart-error">No seasonality data available</div>
            </div>
          </div>

          <!-- Stats del historial -->
          <div class="modal-stats" *ngIf="stockHistory">
            <div class="modal-stat-item">
              <span class="modal-stat-label">Current Price</span>
              <span class="modal-stat-value">\${{ stockHistory.currentPrice | number:'1.2-2' }}</span>
            </div>
            <div class="modal-stat-item">
              <span class="modal-stat-label">24h Change</span>
              <span class="modal-stat-value" [class.positive]="stockHistory.priceChange24h > 0" [class.negative]="stockHistory.priceChange24h < 0">
                {{ stockHistory.priceChange24h > 0 ? '+' : '' }}{{ stockHistory.priceChange24h | number:'1.2-2' }} 
                ({{ stockHistory.priceChangePercent24h | number:'1.2-2' }}%)
              </span>
            </div>
            <div class="modal-stat-item">
              <span class="modal-stat-label">52 Semanas</span>
              <span class="modal-stat-value">
                \${{ stockHistory.low52w | number:'1.2-2' }} - \${{ stockHistory.high52w | number:'1.2-2' }}
              </span>
            </div>
            <div class="modal-stat-item">
              <span class="modal-stat-label">Generated Signal</span>
              <span class="modal-stat-value signal-info">
                \${{ stockHistory.signalGenerated.atPrice | number:'1.2-2' }} 
                <span class="signal-date">({{ stockHistory.signalGenerated.date }})</span>
              </span>
            </div>
          </div>

          <!-- Análisis técnico detallado (después del gráfico) -->
          <div class="modal-section" *ngIf="selectedSignal.reasons && selectedSignal.reasons.length > 0">
            <div class="collapsible-header" (click)="toggleReasonsExpanded()">
              <h3>Technical Details</h3>
              <span class="collapsible-chevron" [class.expanded]="reasonsExpanded">▼</span>
            </div>
            <ul class="reasons-list" [class.collapsed]="!reasonsExpanded">
              <li *ngFor="let reason of selectedSignal.reasons" class="reason-item">
                <span class="reason-dot" [style.background-color]="getReasonCategory(reason).color"></span>
                <span class="reason-text">{{ reason }}</span>
                <span class="reason-badge" [style.border-color]="getReasonCategory(reason).color" [style.color]="getReasonCategory(reason).color">
                  {{ getReasonCategory(reason).label }}
                </span>
              </li>
            </ul>
          </div>

          <!-- Outras acciones -->
          <div class="related-stocks" *ngIf="signals.length > 1">
            <h4>Other actions</h4>
            <div class="related-stocks-grid">
              <div 
                *ngFor="let signal of getRelatedSignals()"
                class="related-stock-btn"
                (click)="openModal(signal); $event.stopPropagation()">
                <div class="card-top">
                  <span class="related-symbol">{{ signal.symbol }}</span>
                  <span class="related-type" [ngClass]="getBadgeClass(signal.signalType)">{{ signal.signalType }}</span>
                </div>
                <div class="card-bottom">
                  <span class="market-pill">{{ signal.market }}</span>
                  <span class="trend" [ngClass]="getTrendClass(signal.trend)">
                    {{ getTrendIcon(signal.trend) }} {{ signal.trend }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <header class="header">
        <div class="logo">
          <svg class="logo-icon" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="18" stroke="white" stroke-width="2.5"/>
            <path d="M20 8L28 28H22L20 24L18 28H12L20 8Z" fill="#00C853"/>
            <path d="M15 18H24L23 12H16L15 18Z" fill="white"/>
          </svg>
          <span class="logo-text">QuantEdge</span>
        </div>
      </header>

      <main class="main-content">
        <section class="stats-section">
          <div class="stat-card buy">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
                <polyline points="17 6 23 6 23 12"></polyline>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ buyCount }}</span>
              <span class="stat-label">BUY Signals</span>
            </div>
          </div>

          <div class="stat-card sell">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline>
                <polyline points="17 18 23 18 23 12"></polyline>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ sellCount }}</span>
              <span class="stat-label">SELL Signals</span>
            </div>
          </div>

          <div class="stat-card hold">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ holdCount }}</span>
              <span class="stat-label">HOLD Signals</span>
            </div>
          </div>

          <div class="stat-card total">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ totalSignals }}</span>
              <span class="stat-label">Total Analyzed</span>
            </div>
          </div>
</section>

        <!-- Fila 1: buscador + filtros -->
        <div class="search-row">
          <div class="search-bar">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.35-4.35"></path>
            </svg>
            <input 
              type="text" 
              class="search-input" 
              placeholder="Search by name..."
              [(ngModel)]="searchQuery"
              (input)="onSearchChange()">
            <button *ngIf="searchQuery" class="clear-search-btn" (click)="clearSearch()">×</button>
          </div>
        </div>
        <div *ngIf="searchError" class="search-error">
          <span>{{ searchError }}</span>
        </div>

        <section class="table-section">
          <div class="table-header">
            <div class="header-row">
              <div class="header-left">
                <h2>Today's Signals</h2>
                <span class="analysis-date" *ngIf="analysisDate">{{ analysisDate }}</span>
              </div>
              <div class="header-controls">
                <button class="filter-btn" title="Filters">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 3v18M3 9h18M3 15h18"/>
                  </svg>
                </button>
                <div class="sort-dropdown">
                <button class="sort-trigger" (click)="toggleSortMenu()" [class.active]="sortMenuOpen || sortConfigs.length > 0" title="Sort">
                  <svg class="sort-icon-svg" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2">
                    <path d="M3 6h18M7 12h10M12 18h2"/>
                  </svg>
                  <span class="sort-count" *ngIf="sortConfigs.length > 1">{{ sortConfigs.length }}</span>
                  <svg class="chevron" [class.open]="sortMenuOpen" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                  </svg>
                </button>
                <div class="sort-menu" *ngIf="sortMenuOpen">
                  <div class="sort-section-title">Add sorting</div>
                  <button 
                    class="sort-option" 
                    [class.active]="isColumnSorted('companyName')"
                    (click)="sortBy('companyName')">
                    Nombre
                    <span class="sort-icon" *ngIf="isColumnSorted('companyName')">
                      {{ isColumnSorted('companyName') === 'asc' ? '↑' : '↓' }}
                    </span>
                  </button>
                  <button 
                    class="sort-option" 
                    [class.active]="isColumnSorted('signalType')"
                    (click)="sortBy('signalType')">
                    Signal
                    <span class="sort-icon" *ngIf="isColumnSorted('signalType')">
                      {{ isColumnSorted('signalType') === 'asc' ? '↑' : '↓' }}
                    </span>
                  </button>
                  <button 
                    class="sort-option" 
                    [class.active]="isColumnSorted('market')"
                    (click)="sortBy('market')">
                    Market
                    <span class="sort-icon" *ngIf="isColumnSorted('market')">
                      {{ isColumnSorted('market') === 'asc' ? '↑' : '↓' }}
                    </span>
                  </button>
                  <button *ngIf="sortConfigs.length > 0" class="clear-sort" (click)="clearSort()">
                    Clear all
                  </button>
                </div>
              </div>
              <button class="filter-btn" title="Filters">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 3v18M3 9h18M3 15h18"/>
                </svg>
              </button>
              <div class="sort-backdrop" *ngIf="sortMenuOpen" (click)="toggleSortMenu()"></div>
              </div>
            </div>
          </div>
          
          <div class="table-container">
            <table class="signals-table">
              <thead>
                <tr>
                  <th class="sortable" (click)="sortBy('companyName', $event)" style="width: 220px;">
                    <span class="th-text">Name</span>
                    <span class="th-sort-icon" *ngIf="isColumnSorted('companyName')">
                      {{ isColumnSorted('companyName') === 'asc' ? '↑' : '↓' }}
                    </span>
                  </th>
                  <th class="sortable" (click)="sortBy('market', $event)">
                    <span class="th-text">Market</span>
                    <span class="th-sort-icon" *ngIf="isColumnSorted('market')">
                      {{ isColumnSorted('market') === 'asc' ? '↑' : '↓' }}
                    </span>
                  </th>
                  <th class="sortable" (click)="sortBy('signalType', $event)">
                    <span class="th-text">Signal</span>
                    <span class="th-sort-icon" *ngIf="isColumnSorted('signalType')">
                      {{ isColumnSorted('signalType') === 'asc' ? '↑' : '↓' }}
                    </span>
                  </th>
                  <th>Trend</th>
                  <th>Price</th>
                  <th>24h Change %</th>
                  <th>VOL</th>
                  <th style="width: 220px;">Sector</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let signal of sortedSignals" [class]="signal.signalType.toLowerCase()" (click)="openModal(signal)" class="clickable-row">
                  <td class="company-cell">
                    <div class="table-company-info">
                      <img *ngIf="signal.logoUrl" [src]="signal.logoUrl" alt="Logo" class="table-company-logo" (error)="onTableLogoError($event, signal)">
                      <span *ngIf="!signal.logoUrl" class="table-company-logo-fallback">📊</span>
                      <div class="table-company-text">
                        <span class="table-company-name">{{ signal.companyName || signal.symbol }}</span>
                        <span class="table-company-ticker">{{ signal.symbol }}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="market-tag" [class]="signal.market.toLowerCase()">
                      {{ signal.market }}
                    </span>
                  </td>
                  <td>
                    <span class="signal-badge" [class]="signal.signalType.toLowerCase()">
                      {{ signal.signalType }}
                    </span>
                  </td>
                  <td>
                    <span class="trend-indicator" [class.alcista]="signal.trend === 'ALCISTA'" [class.bajista]="signal.trend === 'BAJISTA'" [class.lateral]="signal.trend === 'LATERAL'">
                      <span class="trend-dot" [class.alcista]="signal.trend === 'ALCISTA'" [class.bajista]="signal.trend === 'BAJISTA'" [class.lateral]="signal.trend === 'LATERAL'"></span>
                      {{ signal.trend }}
                    </span>
                   </td>
                    <td class="price-cell">\${{ signal.price | number:'1.2-2' }}</td>
                    <td class="change-cell" [class.positive]="signal.priceChangePercent24h > 0 && signal.price > 0" [class.negative]="signal.priceChangePercent24h < 0 && signal.price > 0">
                      <span *ngIf="signal.price > 0 && signal.priceChangePercent24h > 0">+</span>{{ signal.price > 0 ? (signal.priceChangePercent24h | number:'1.2-2') + '%' : '-' }}</td>
                    <td>
                      <span class="volume-badge" 
                        [class.high]="(signal.volumeRelative ?? 1) > 1.5" 
                        [class.normal]="(signal.volumeRelative ?? 1) >= 0.8 && (signal.volumeRelative ?? 1) <= 1.5"
                        [class.low]="(signal.volumeRelative ?? 1) < 0.8">
                        {{ signal.volumeRelative ?? 1 | number:'1.1-1' }}x
                      </span>
                    </td>
                    <td class="sector-cell">{{ signal.sector || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div *ngIf="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading signals...</p>
          </div>

          <div #scrollSentinel class="scroll-sentinel"></div>

          <div *ngIf="error" class="error-state">
            <div class="error-icon">⚠️</div>
            <h3>Error</h3>
            <p>{{ error }}</p>
            <button class="retry-btn" (click)="loadSignals()">Retry</button>
          </div>

          <div *ngIf="!loading && !error && signals.length === 0" class="empty-state">
            <div class="empty-icon">📊</div>
            <h3>No signals for today</h3>
            <p>Run analysis from the Python service to get signals.</p>
          </div>
        </section>

        <div class="disclaimer-footer">
          ⚠ Technical analysis only · Not financial advice · DYOR
        </div>
      </main>
    </div>
  `,
  styles: [`
    :host {
      --bg-primary: #0B0F19;
      --bg-card: #111827;
      --bg-elevated: #1F2937;
      --border: #1F2937;
      
      --text-primary: #E5E7EB;
      --text-secondary: #9CA3AF;
      --text-muted: #6B7280;
      
      --buy: #22C55E;
      --sell: #EF4444;
      --hold: #F59E0B;
      --accent: #3B82F6;
      
      --buy-glow: rgba(34, 197, 94, 0.15);
      --sell-glow: rgba(239, 68, 68, 0.15);
      --hold-glow: rgba(245, 158, 11, 0.15);
      --accent-glow: rgba(59, 130, 246, 0.15);
      
      display: block;
      min-height: 100vh;
      background: var(--bg-primary);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .dashboard {
      min-height: 100vh;
      background: radial-gradient(ellipse at top, #111827 0%, #0B0F19 50%);
    }

    .header {
      background: rgba(17, 24, 39, 0.8);
      backdrop-filter: blur(12px);
      padding: 24px 40px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .logo-icon {
      width: 38px;
      height: 38px;
    }

    .logo-text {
      font-size: 28px;
      font-weight: 700;
      color: #fff;
      letter-spacing: -1.5px;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main-content {
      padding: 40px 48px;
      max-width: 1800px;
      margin: 0 auto;
    }

    .stats-section {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 24px;
      margin-bottom: 40px;
    }

    .stat-card {
      background: var(--bg-card);
      border-radius: 20px;
      padding: 28px;
      display: flex;
      align-items: center;
      gap: 20px;
      border: 1px solid var(--border);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }

    .stat-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: transparent;
      transition: background 0.3s ease;
    }

    .stat-card.buy::before { background: var(--buy); }
    .stat-card.sell::before { background: var(--sell); }
    .stat-card.hold::before { background: var(--hold); }
    .stat-card.total::before { background: var(--accent); }

    .stat-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .stat-card.buy:hover { box-shadow: 0 12px 40px rgba(34, 197, 94, 0.15); }
    .stat-card.sell:hover { box-shadow: 0 12px 40px rgba(239, 68, 68, 0.15); }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .stat-card.buy .stat-icon { background: var(--buy-glow); color: var(--buy); }
    .stat-card.sell .stat-icon { background: var(--sell-glow); color: var(--sell); }
    .stat-card.hold .stat-icon { background: var(--hold-glow); color: var(--hold); }
    .stat-card.total .stat-icon { background: var(--accent-glow); color: var(--accent); }

    .stat-icon svg {
      width: 26px;
      height: 26px;
    }

    .stat-info {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .stat-value {
      font-size: 36px;
      font-weight: 700;
      color: #fff;
      line-height: 1;
      letter-spacing: -1px;
    }

    .stat-label {
      font-size: 14px;
      color: var(--text-secondary);
      font-weight: 500;
    }

    .table-section {
      background: var(--bg-card);
      border-radius: 24px;
      padding: 20px;
      border: 1px solid var(--border);
    }

    .table-header {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 28px;
    }

    .header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
    }

    .header-row h2 {
      font-size: 22px;
      font-weight: 600;
      color: #fff;
      margin: 0;
      letter-spacing: -0.5px;
    }

    .header-left {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .header-left h2 {
      font-size: 22px;
      font-weight: 600;
      color: #fff;
      margin: 0;
    }

    .analysis-date {
      font-size: 14px;
      color: #9CA3AF;
    }

    .header-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .search-row {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }

    .search-row .search-bar {
      flex: 1;
    }

    .search-bar {
      display: flex;
      align-items: center;
      background: #1F2937;
      border-radius: 8px;
      padding: 8px 12px;
      gap: 8px;
      width: 200px;
    }

    .search-bar .search-icon {
      width: 18px;
      height: 18px;
      color: #9CA3AF;
    }

    .search-bar .search-input {
      border: none;
      background: transparent;
      outline: none;
      font-size: 14px;
      color: #fff;
      width: 100%;
    }

    .search-bar .search-input::placeholder {
      color: #9CA3AF;
    }

    .clear-search-btn {
      background: rgba(255,255,255,0.1);
      border: none;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      color: #9CA3AF;
      font-size: 16px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .clear-search-btn:hover {
      background: rgba(255,255,255,0.2);
      color: #fff;
    }

    .search-error {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 6px;
      padding: 8px 12px;
      margin-bottom: 12px;
      font-size: 13px;
      color: #FCA5A5;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .filter-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: #1F2937;
      border: none;
      border-radius: 8px;
      cursor: pointer;
    }

    .filter-btn svg {
      width: 18px;
      height: 18px;
      stroke: #9CA3AF;
    }

    @media (max-width: 640px) {
      .header-row {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
      }

      .header-right {
        width: 100%;
      }

      .search-bar {
        flex: 1;
      }
    }

    .sort-dropdown {
      position: relative;
    }

    .table-controls {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .table-subtitle {
      font-size: 14px;
      color: var(--text-muted);
    }

    .sort-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .sort-label {
      font-size: 12px;
      color: var(--text-muted);
    }

    .sort-trigger {
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      padding: 8px 10px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }

    .sort-trigger svg {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
    }

    .sort-icon {
      font-size: 12px;
      font-weight: 700;
    }

.sort-dropdown {
      position: relative;
    }

    .sort-menu {
      position: absolute;
      right: 0 !important;
      left: auto !important;
      width: 160px;
      top: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 8px;
      min-width: 160px;
      max-width: 90vw;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      z-index: 100;
      animation: fadeIn 0.2s ease;
    }

    .sort-option {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      background: transparent;
      border: none;
      color: var(--text-secondary);
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .sort-option:hover {
      background: var(--bg-elevated);
      color: var(--text-primary);
    }

    .sort-option.active {
      background: rgba(59, 130, 246, 0.15);
      color: var(--accent);
    }

    .sort-option:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .sort-option:disabled:hover {
      background: transparent;
      color: var(--text-secondary);
    }

    .sort-section-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 8px 14px 4px;
    }

    .active-sorts {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 4px;
    }

    .active-sort {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(59, 130, 246, 0.1);
      color: var(--accent);
      padding: 8px 12px;
    }

    .active-sort:hover {
      background: rgba(59, 130, 246, 0.15);
      color: var(--accent);
    }

    .remove-sort {
      background: transparent;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 2px 6px;
      font-size: 12px;
      border-radius: 4px;
      transition: all 0.2s ease;
    }

    .remove-sort:hover {
      background: rgba(239, 68, 68, 0.2);
      color: var(--sell);
    }

    .clear-sort {
      width: 100%;
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-secondary);
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 13px;
      cursor: pointer;
      margin-top: 8px;
      transition: all 0.2s ease;
    }

    .clear-sort:hover {
      background: rgba(239, 68, 68, 0.1);
      border-color: var(--sell);
      color: var(--sell);
    }

    .sort-count {
      background: var(--accent);
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 10px;
      min-width: 18px;
      text-align: center;
    }

    .sort-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 99;
    }

    .signals-table th.sortable {
      cursor: pointer;
      user-select: none;
      transition: color 0.2s ease;
      white-space: nowrap;
    }

    .signals-table th.sortable:hover {
      color: var(--accent);
    }

    .signals-table th.sortable .th-text {
      display: inline-block;
      vertical-align: middle;
    }

    .th-sort-icon {
      display: inline-block;
      font-size: 12px;
      color: var(--accent);
      vertical-align: middle;
      margin-left: 6px;
    }

    .table-container {
      overflow-x: auto;
      border-radius: 12px;
    }

    .signals-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
    }

    .signals-table th {
      text-align: left;
      padding: 16px 20px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      background: var(--bg-elevated);
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }

    .signals-table th:first-child {
      border-radius: 12px 0 0 0;
    }

    .signals-table th:last-child {
      border-radius: 0 12px 0 0;
    }

    .signals-table td {
      padding: 18px 20px;
      font-size: 14px;
      color: var(--text-primary);
      border-bottom: 1px solid var(--border);
      background: transparent;
      transition: background 0.2s ease;
    }

    .signals-table tbody tr {
      transition: all 0.2s ease;
    }

    .signals-table tbody tr:hover td {
      background: rgba(59, 130, 246, 0.05);
    }

    .signals-table tbody tr:last-child td {
      border-bottom: none;
    }

    .signals-table tbody tr:last-child td:first-child {
      border-radius: 0 0 0 12px;
    }

    .signals-table tbody tr:last-child td:last-child {
      border-radius: 0 0 12px 0;
    }

    .company-cell {
      padding: 12px 16px !important;
    }

    .table-company-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .table-company-logo {
      width: 36px;
      height: 36px;
      border-radius: 6px;
      object-fit: contain;
      background: #fff;
      border: 2px solid #000;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
      flex-shrink: 0;
    }

    .table-company-logo-fallback {
      width: 36px;
      height: 36px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-elevated);
      border: 2px solid #000;
      font-size: 18px;
      flex-shrink: 0;
    }

    .table-company-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }

    .table-company-name {
      font-size: 16px;
      font-weight: 500;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .table-company-ticker {
      font-size: 12px;
      color: #4a5568;
      white-space: nowrap;
    }

    .market-tag {
      display: inline-flex;
      align-items: center;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.5px;
    }

    .market-tag.us { 
      background: rgba(59, 130, 246, 0.15); 
      color: #60A5FA; 
    }
    .market-tag.ar { 
      background: rgba(251, 191, 36, 0.15); 
      color: #FBBF24; 
    }
    .market-tag.eu { 
      background: rgba(168, 85, 247, 0.15); 
      color: #A855F7; 
    }
    .market-tag.jp { 
      background: rgba(244, 63, 94, 0.15); 
      color: #F43F5E; 
    }

    .signal-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }

    .signal-badge.buy { 
      background: var(--buy); 
      color: #000; 
    }
    .signal-badge.buy::before {
      content: '▲';
      font-size: 8px;
    }
    .signal-badge.sell { 
      background: var(--sell); 
      color: #fff; 
    }
    .signal-badge.sell::before {
      content: '▼';
      font-size: 8px;
    }
    .signal-badge.hold { 
      background: var(--hold); 
      color: #000; 
    }

    .price-cell {
      font-weight: 600;
      color: #fff !important;
      font-variant-numeric: tabular-nums;
    }

    .change-cell {
      font-weight: 600;
      font-size: 13px;
      font-variant-numeric: tabular-nums;
    }

    .rsi-cell {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .rsi-value {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      min-width: 28px;
    }

    .rsi-bar-container {
      width: 40px;
      height: 6px;
      background: var(--bg-elevated);
      border-radius: 3px;
      overflow: hidden;
    }

    .rsi-bar {
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease, background 0.3s ease;
    }

    .rsi-bar.oversold { background: var(--buy); }
    .rsi-bar.neutral { background: var(--hold); }
    .rsi-bar.overbought { background: var(--sell); }

    .sector-cell {
      font-size: 12px;
      color: var(--text-secondary);
      max-width: 220px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .volume-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
    }

    .volume-badge.high {
      color: var(--buy);
      background: var(--buy-glow);
    }

    .volume-badge.normal {
      color: var(--text-muted);
      background: rgba(107, 114, 128, 0.15);
    }

    .volume-badge.low {
      color: var(--hold);
      background: var(--hold-glow);
    }

    .positive { color: var(--buy) !important; }
    .negative { color: var(--sell) !important; }

    .trend-indicator {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
    }

    .trend-indicator.alcista { 
      color: var(--buy); 
      background: var(--buy-glow);
    }
    .trend-indicator.bajista { 
      color: var(--sell); 
      background: var(--sell-glow);
    }
    .trend-indicator.lateral { 
      color: var(--text-secondary); 
      background: var(--bg-elevated);
    }

    .trend-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--text-muted);
    }

.trend-dot.alcista {
      background: var(--buy);
      box-shadow: 0 0 8px var(--buy);
    }
    .trend-dot.bajista {
      background: var(--sell);
      box-shadow: 0 0 8px var(--sell);
    }
    .trend-dot.lateral {
      background: var(--text-muted);
      box-shadow: none;
    }

    /* Modal */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      animation: fadeIn 0.2s ease;
    }

    .modal-content {
      background: var(--bg-card);
      border-radius: 24px;
      padding: 28px;
      max-width: 540px;
      width: 92%;
      max-height: 85vh;
      overflow-y: auto;
      position: relative;
      border: 1px solid var(--border);
      animation: slideUp 0.3s ease;
    }

    .modal-content.modal-large {
      max-width: 800px;
    }

    .modal-close {
      display: none;
    }

    .modal-close-small {
      display: flex;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
      position: relative;
    }

    .modal-metadata {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }

    .meta-badge {
      background: var(--bg-elevated);
      color: var(--text-secondary);
      padding: 4px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      border: 1px solid var(--border);
    }

    .meta-badge.market-cap {
      color: var(--accent);
      border-color: rgba(59, 130, 246, 0.3);
    }

    .modal-header h2 {
      margin: 0;
      font-size: 22px;
      color: #fff;
    }

    .modal-symbol {
      color: var(--text-secondary);
      font-size: 13px;
    }

    .modal-company-info {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .modal-title-section {
      display: flex;
      flex-direction: column;
    }

    .company-logo {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      object-fit: contain;
      background: #fff;
      padding: 4px;
    }

    .company-logo-container {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-elevated);
    }

    .company-logo-fallback {
      font-size: 24px;
    }

    .recommendation {
      padding: 12px 16px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 20px;
      line-height: 1.4;
    }

    .recommendation.buy {
      background: rgba(34, 197, 94, 0.15);
      color: var(--buy);
      border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .recommendation.sell {
      background: rgba(239, 68, 68, 0.15);
      color: var(--sell);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .recommendation.hold {
      background: rgba(245, 158, 11, 0.15);
      color: var(--hold);
      border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .ema-legend {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 12px;
      font-size: 12px;
      color: var(--text-secondary);
    }

    .ema-legend .ema-item {
      padding: 6px 12px;
      background: var(--bg-elevated);
      border-radius: 6px;
    }

    .chart-toggles {
      display: flex;
      justify-content: flex-end;
      gap: 16px;
      margin-bottom: 8px;
      padding-right: 8px;
    }

    .chart-toggle {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      font-size: 12px;
      color: var(--text-secondary);
    }

    .chart-toggle input {
      cursor: pointer;
    }

    .toggle-label {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .color-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
    }

    .color-dot.green {
      background: #22C55E;
    }

    .color-dot.blue {
      background: #3B82F6;
    }

    .color-dot.white {
      background: #ffffff;
      border: 1px solid #6B7280;
    }

    .modal-close-btn {
      background: var(--bg-elevated);
      border: none;
      color: var(--text-secondary);
      font-size: 16px;
      cursor: pointer;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      transition: all 0.2s ease;
      margin-top: -4px;
    }

    .modal-close-btn:hover {
      background: rgba(255,255,255,0.1);
      color: #fff;
    }

    .modal-signal-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 8px 20px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 700;
      margin-bottom: 20px;
    }

    .modal-signal-pill.buy {
      background: var(--buy);
      color: #000;
    }

    .modal-signal-pill.sell {
      background: var(--sell);
      color: #fff;
    }

    .modal-signal-pill.hold {
      background: var(--hold);
      color: #000;
    }

    .modal-recommendation-text {
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.5;
      margin: 0 0 16px 0;
    }

    .modal-section {
      margin-bottom: 16px;
      background: var(--bg-elevated);
      padding: 16px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }

    .modal-section h3 {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--text-muted);
      margin: 0 0 8px;
    }

    .collapsible-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      margin-bottom: 8px;
      padding-top: 2px;
    }

    .collapsible-header h3 {
      margin: 0;
      line-height: 1;
      display: inline-block;
    }

    .collapsible-chevron {
      font-size: 10px;
      color: var(--text-muted);
      transition: transform 0.2s ease;
      padding-top: 4px;
    }

    .collapsible-chevron.expanded {
      transform: rotate(180deg);
    }

    .reasons-list.collapsed {
      max-height: 0;
      overflow: hidden;
      opacity: 0;
    }

    .reasons-list:not(.collapsed) {
      max-height: 600px;
      overflow: hidden;
      transition: max-height 0.3s ease, opacity 0.2s ease;
      opacity: 1;
    }

    .analysis-text {
      color: var(--text-primary);
      font-size: 13px;
      line-height: 1.5;
      margin: 0;
    }

    .reasons-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .reason-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      border-radius: 6px;
      background: #0d1117;
      border: 0.5px solid #1a2030;
    }

    .reason-item:hover {
      background: #111927;
    }

    .reason-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .reason-text {
      flex: 1;
      font-size: 12px;
      color: #c9d4e0;
      line-height: 1.4;
    }

    .reason-badge {
      font-size: 9px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 12px;
      border: 1px solid;
      background: transparent;
      white-space: nowrap;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .modal-stats {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 20px;
    }

    .modal-stat-item {
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: #111927;
      border-radius: 8px;
      padding: 14px 16px;
      border: 0.5px solid #1a2030;
    }

    .modal-stat-label {
      font-size: 10px;
      font-weight: 500;
      color: #4a5568;
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }

    .modal-stat-value {
      font-size: 20px;
      font-weight: 500;
      color: #c9d4e0;
      font-family: 'IBM Plex Mono', monospace;
    }

    .modal-stat-value.positive { color: #22c55e; }
    .modal-stat-value.negative { color: #ef4444; }

    .related-stocks {
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
    }

    .related-stocks h4 {
      font-size: 14px;
      color: var(--text-secondary);
      margin: 0 0 12px;
      font-weight: 500;
    }

    .related-stocks-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .related-stock-btn {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 10px 12px;
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .related-stock-btn:hover {
      background: rgba(59, 130, 246, 0.1);
      border-color: var(--accent);
    }

    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .card-bottom {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .market-pill {
      font-size: 11px;
      color: #64748b;
      background: rgba(100, 116, 139, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .trend {
      font-size: 11px;
      font-weight: 500;
    }

    .trend-up { color: #22c55e; }
    .trend-down { color: #ef4444; }
    .trend-neu { color: #64748b; }

    .badge-buy {
      background: rgba(34, 197, 94, 0.15);
      color: #22c55e;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .badge-sell {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .badge-hold {
      background: rgba(245, 158, 11, 0.15);
      color: #f59e0b;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .related-symbol {
      font-size: 13px;
      font-weight: 600;
      color: #fff;
    }

    .related-type {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 600;
    }

    .related-type.buy {
      background: rgba(0, 200, 83, 0.2);
      color: var(--buy);
    }

    .related-type.sell {
      background: rgba(244, 67, 54, 0.2);
      color: var(--sell);
    }

    .related-type.hold {
      background: rgba(255, 193, 7, 0.2);
      color: var(--hold);
    }

    .chart-section {
      margin-bottom: 20px;
    }

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .chart-header h3 {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }

    .period-selector {
      display: flex;
      gap: 8px;
    }

    .period-selector button {
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .period-selector button:hover {
      background: rgba(59, 130, 246, 0.1);
      border-color: var(--accent);
      color: var(--text-primary);
    }

    .period-selector button.active {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }

    .chart-container {
      height: 400px;
      background: var(--bg-elevated);
      border-radius: 8px;
      padding: 4px 24px 32px 24px;
    }

    .chart-loading,
    .chart-error {
      height: 400px;
      background: var(--bg-elevated);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      color: var(--text-secondary);
      font-size: 14px;
    }

    .chart-error {
      color: var(--sell);
    }

    .spinner-small {
      width: 20px;
      height: 20px;
      border: 2px solid var(--bg-card);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    .signal-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .signal-date {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 400;
    }

    @keyframes slideUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .clickable-row {
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .clickable-row:hover {
      background: rgba(59, 130, 246, 0.1) !important;
    }

    .clickable-row:hover td {
      color: #fff;
    }

    .clickable-row .company-cell {
      position: relative;
      padding-right: 24px !important;
    }

    .clickable-row .company-cell::after {
      content: '›';
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--accent);
      font-size: 18px;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    .clickable-row:hover .company-cell::after {
      opacity: 1;
    }

    .table-hint {
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .empty-state,
    .loading-state {
      text-align: center;
      padding: 80px 24px;
    }

    .loading-state .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid var(--bg-elevated);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 16px;
    }

    .loading-state p,
    .empty-state p {
      color: var(--text-secondary);
      margin: 0;
      font-size: 15px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .empty-icon {
      font-size: 64px;
      margin-bottom: 20px;
      opacity: 0.6;
    }

    .empty-state h3 {
      color: #fff;
      font-size: 20px;
      margin: 0 0 12px;
      font-weight: 600;
    }

    .error-state {
      text-align: center;
      padding: 60px 24px;
      background: var(--bg-card);
      border-radius: 16px;
      margin-top: 20px;
    }

    .error-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    .error-state h3 {
      color: var(--sell);
      font-size: 20px;
      margin: 0 0 8px;
      font-weight: 600;
    }

    .error-state p {
      color: var(--text-secondary);
      margin: 0 0 20px;
      font-size: 14px;
    }

    .retry-btn {
      background: var(--accent);
      color: #fff;
      border: none;
      padding: 10px 24px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }

    .retry-btn:hover {
      background: #2563eb;
    }

    .scroll-sentinel {
      height: 1px;
      width: 100%;
    }

    .loading-more {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 24px;
      color: var(--text-secondary);
      font-size: 14px;
    }

    .spinner-small {
      width: 20px;
      height: 20px;
      border: 2px solid var(--bg-elevated);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    /* Focus states for accessibility */
    .clickable-row:focus {
      outline: 2px solid var(--accent);
      outline-offset: -2px;
    }

    .clickable-row:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: -2px;
    }

    .modal-close-btn:focus {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }

    .modal-overlay:focus {
      outline: none;
    }

    @media (max-width: 1400px) {
      .stats-section {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media (max-width: 768px) {
      .header {
        padding: 20px 24px;
      }
      
      .main-content {
        padding: 24px;
      }

      .stats-section {
        grid-template-columns: 1fr;
        gap: 16px;
      }

      .stat-card {
        padding: 20px;
      }

      .stat-value {
        font-size: 28px;
      }

      .table-section {
        padding: 20px;
        border-radius: 16px;
      }

      .table-header {
        flex-direction: column;
        gap: 16px;
      }

      .header-row {
        width: 100%;
        justify-content: space-between;
      }

      .sort-menu {
        right: 0 !important;
        left: auto !important;
      }

      .signals-table th,
      .signals-table td {
        padding: 12px 14px;
      }

      .disclaimer-banner {
        background: #374151;
        color: #e5e7eb;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        font-size: 14px;
        flex-wrap: wrap;
      }

      .disclaimer-banner span {
        text-align: center;
      }

      .disclaimer-btn {
        background: #6b7280;
        color: #fff;
        border: none;
        padding: 8px 20px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }

.disclaimer-btn:hover {
        background: #4b5563;
      }

      .disclaimer-footer {
        background: #1f2937;
        color: #9ca3af;
        padding: 10px 20px;
        text-align: center;
        font-size: 12px;
        border-top: 1px solid #374151;
        margin-top: 20px;
      }
    }
    `]
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('scrollSentinel') scrollSentinel!: ElementRef;
  
  @ViewChild('seasonalityChart') seasonalityChartRef!: ElementRef;
  
  signals: Signal[] = [];
  selectedSignal: Signal | null = null;
  stockHistory: StockHistory | null = null;
  loading = false;
  loadingMore = false;
  loadingHistory = false;
  loadingSeasonality = false;
  historyError: string | null = null;
  error: string | null = null;
  totalSignals = 0;
  buyCount = 0;
  sellCount = 0;
  holdCount = 0;
  
  selectedPeriod: number = 60;
  reasonsExpanded: boolean = false;
  logoLoaded = false;
  
  // Seasonality chart
  seasonalityData: any = null;
  private seasonalityChart: Chart | null = null;

  
  
  sortColumn: SortColumn = null;
  sortDirection: SortDirection = null;
  sortMenuOpen = false;
  sortConfigs: SortConfig[] = [];
  
  searchQuery = '';
  searchError = '';
  analysisDate = '';
  
  private currentPage = 0;
  private pageSize = 100;
  private totalPages = 1;
  private hasMore = true;
  private observer: IntersectionObserver | null = null;
  private destroyRef = inject(DestroyRef);
  

  constructor(private signalService: SignalService) {}

  get sortedSignals(): Signal[] {
    let result = this.signals;
    
    // Filter by search query
    if (this.searchQuery && this.searchQuery.trim()) {
      const query = this.searchQuery.toLowerCase().trim();
      result = result.filter(s => 
        (s.companyName && s.companyName.toLowerCase().includes(query))
      );
    }
    
    if (this.sortConfigs.length === 0 && (!this.sortColumn || !this.sortDirection)) {
      return result;
    }
    
    const configs = [...this.sortConfigs];
    if (this.sortColumn && this.sortDirection) {
      configs.push({ column: this.sortColumn, direction: this.sortDirection });
    }
    
    if (configs.length === 0) return this.signals;
    
    return [...this.signals].sort((a, b) => {
      for (const config of configs) {
        let comparison = 0;
        
        if (config.column === 'companyName') {
          const nameA = (a.companyName || a.symbol || '').toLowerCase();
          const nameB = (b.companyName || b.symbol || '').toLowerCase();
          comparison = nameA.localeCompare(nameB);
        } else if (config.column === 'signalType') {
          const signalOrder: Record<string, number> = { 'BUY': 1, 'SELL': 3, 'HOLD': 2 };
          comparison = signalOrder[a.signalType] - signalOrder[b.signalType];
        } else if (config.column === 'market') {
          const marketOrder: Record<string, number> = { 'AR': 1, 'US': 2, 'EU': 3, 'JP': 4 };
          comparison = (marketOrder[a.market] || 4) - (marketOrder[b.market] || 4);
        }
        
        if (comparison !== 0) {
          return config.direction === 'asc' ? comparison : -comparison;
        }
      }
      return 0;
    });
  }

  sortBy(column: 'companyName' | 'signalType' | 'market', event?: MouseEvent): void {
    const existingIndex = this.sortConfigs.findIndex(c => c.column === column);
    
    if (existingIndex >= 0) {
      const existing = this.sortConfigs[existingIndex];
      if (existing.direction === 'asc') {
        this.sortConfigs[existingIndex].direction = 'desc';
      } else {
        this.sortConfigs.splice(existingIndex, 1);
      }
    } else {
      this.sortConfigs.push({ column, direction: 'asc' });
      if (this.sortConfigs.length > 3) {
        this.sortConfigs.shift();
      }
    }
    
    this.sortColumn = this.sortConfigs.length > 0 ? this.sortConfigs[this.sortConfigs.length - 1].column : null;
    this.sortDirection = this.sortConfigs.length > 0 ? this.sortConfigs[this.sortConfigs.length - 1].direction : null;
  }

  isColumnSorted(column: string): 'asc' | 'desc' | null {
    const config = this.sortConfigs.find(c => c.column === column);
    return config ? config.direction : null;
  }

  clearSort(): void {
    this.sortConfigs = [];
    this.sortColumn = null;
    this.sortDirection = null;
  }

  getColumnLabel(column: string): string {
    const labels: Record<string, string> = {
      'companyName': 'Nombre',
      'signalType': 'Signal',
      'market': 'Market',
    };
    return labels[column] || column;
  }

  getRsiClass(rsi: number): string {
    if (rsi < 30) return 'oversold';
    if (rsi > 70) return 'overbought';
    return 'neutral';
  }

  removeSort(column: string, event: MouseEvent): void {
    event.stopPropagation();
    const index = this.sortConfigs.findIndex(c => c.column === column);
    if (index >= 0) {
      this.sortConfigs.splice(index, 1);
      this.sortColumn = this.sortConfigs.length > 0 ? this.sortConfigs[this.sortConfigs.length - 1].column : null;
      this.sortDirection = this.sortConfigs.length > 0 ? this.sortConfigs[this.sortConfigs.length - 1].direction : null;
    }
  }

  toggleSortMenu(): void {
    this.sortMenuOpen = !this.sortMenuOpen;
  }

  onSearchChange(): void {
    this.searchError = '';
    
    if (!this.searchQuery || !this.searchQuery.trim()) {
      return;
    }
    
    const filtered = this.signals.filter(s => 
      s.companyName && s.companyName.toLowerCase().includes(this.searchQuery.toLowerCase().trim())
    );
    
    if (filtered.length === 0) {
      this.searchError = 'No results found. Try a different name.';
    }
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.searchError = '';
  }

  ngOnInit(): void {
    this.loadSignals();
  }

  ngAfterViewInit(): void {
    this.setupIntersectionObserver();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    document.body.style.overflow = '';
  }

  private setupIntersectionObserver(): void {
    this.observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !this.loadingMore && this.hasMore) {
          this.loadMoreSignals();
        }
      },
      { threshold: 0.1 }
    );
    
    if (this.scrollSentinel?.nativeElement) {
      this.observer.observe(this.scrollSentinel.nativeElement);
    }
  }

  @HostListener('document:keydown.escape')
  onEscapePress(): void {
    if (this.selectedSignal) {
      this.closeModal();
    }
  }

  loadSignals(): void {
    this.loading = true;
    this.error = null;
    this.currentPage = 0;
    
    this.signalService.getSignals(0, this.pageSize)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.signals = data.content;
          this.totalSignals = data.totalElements;
          this.totalPages = data.totalPages;
          this.hasMore = !data.last;
          this.loading = false;
          
          // Get analysis date from first signal
          if (data.content.length > 0 && data.content[0].analyzedAt) {
            const date = new Date(data.content[0].analyzedAt);
            this.analysisDate = date.toLocaleDateString('en-US', { 
              month: 'short', day: 'numeric', year: 'numeric' 
            });
          }
        },
        error: (err) => {
          console.error('Error loading signals', err);
          this.error = 'Error loading signals. Try again.';
          this.loading = false;
        }
      });
    
    this.signalService.getTodaySignals()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (allSignals) => {
          this.buyCount = allSignals.filter(s => s.signalType === 'BUY').length;
          this.sellCount = allSignals.filter(s => s.signalType === 'SELL').length;
          this.holdCount = allSignals.filter(s => s.signalType === 'HOLD').length;
        }
      });
  }

  loadMoreSignals(): void {
    if (this.loadingMore || !this.hasMore) return;
    
    this.loadingMore = true;
    this.currentPage++;
    
    this.signalService.getSignals(this.currentPage, this.pageSize)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.signals = [...this.signals, ...data.content];
          this.hasMore = !data.last;
          this.loadingMore = false;
        },
        error: (err) => {
          console.error('Error loading more signals', err);
          this.currentPage--;
          this.loadingMore = false;
        }
      });
  }

  openModal(signal: Signal): void {
    if (signal.reasons && typeof signal.reasons === 'string') {
      try {
        signal.reasons = JSON.parse(signal.reasons);
      } catch {
        signal.reasons = [];
      }
    }
    this.selectedSignal = signal;
    this.stockHistory = null;
    this.historyError = null;
    this.logoLoaded = false;
    this.selectedPeriod = this.getSavedPeriod();
    this.seasonalityData = null;
    this.loadingSeasonality = true;
    this.loadingHistory = true;
    document.body.style.overflow = 'hidden';
    this.loadStockHistory(signal.symbol);
    
    // Scroll al inicio del modal
    setTimeout(() => {
      const modalContent = document.querySelector('.modal-content');
      if (modalContent) {
        (modalContent as HTMLElement).scrollTop = 0;
      }
    }, 10);
  }

  closeModal(): void {
    this.selectedSignal = null;
    this.stockHistory = null;
    this.historyError = null;
    this.seasonalityData = null;
    if (this.seasonalityChart) {
      this.seasonalityChart.destroy();
      this.seasonalityChart = null;
    }
    document.body.style.overflow = '';
  }

  loadStockHistory(symbol: string): void {
    this.historyError = null;
    this.stockHistory = null;
    this.seasonalityData = null;
    this.loadingHistory = true;
    this.loadingSeasonality = true;
    
    this.signalService.getStockHistory(symbol, this.selectedPeriod)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          this.stockHistory = data;
          this.loadingHistory = false;
        },
        error: (err) => {
          console.error('Error loading stock history:', err);
          this.historyError = `Could not load history for ${symbol}. Try another symbol.`;
          this.loadingHistory = false;
        }
      });

    this.signalService.getStockSeasonality(symbol)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          console.log('Seasonality data received:', data);
          this.seasonalityData = data;
          this.loadingSeasonality = false;
          setTimeout(() => this.createSeasonalityChart(), 100);
        },
        error: (err) => {
          console.error('Error loading seasonality:', err);
          this.loadingSeasonality = false;
        }
      });
  }

  changePeriod(days: number): void {
    this.selectedPeriod = days;
    localStorage.setItem('selectedPeriod', days.toString());
    if (this.selectedSignal) {
      this.loadStockHistory(this.selectedSignal.symbol);
    }
  }

  private getSavedPeriod(): number {
    const saved = localStorage.getItem('selectedPeriod');
    return saved ? parseInt(saved, 10) : 60;
  }

  formatMarketCap(cap: number): string {
    if (!cap) return '';
    if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
    if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`;
    if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`;
    return `$${cap.toLocaleString()}`;
  }

  createSeasonalityChart(): void {
    if (!this.seasonalityData || !this.seasonalityChartRef) return;

    if (this.seasonalityChart) {
      this.seasonalityChart.destroy();
    }

    const ctx = this.seasonalityChartRef.nativeElement.getContext('2d');
    const data2026 = this.seasonalityData.yearlyReturns['2026'] || [];
    const data2025 = this.seasonalityData.yearlyReturns['2025'] || [];
    const months = this.seasonalityData.months || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

    this.seasonalityChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: months,
        datasets: [
          {
            label: '2025',
            data: data2025,
            borderColor: '#F59E0B',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            tension: 0.4,
            pointRadius: 3,
            pointBackgroundColor: '#F59E0B',
            pointBorderWidth: 0,
            pointHoverRadius: 5
          },
          {
            label: '2026',
            data: data2026,
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#3B82F6',
            pointBorderWidth: 0,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1500,
          easing: 'easeOutQuart'
        },
        plugins: {
          legend: { 
            display: true,
            position: 'top',
            align: 'end',
            labels: {
              color: '#9CA3AF',
              usePointStyle: true,
              padding: 12,
              font: { size: 12 }
            }
          },
          tooltip: {
            backgroundColor: '#1F2937',
            titleColor: '#fff',
            bodyColor: '#9CA3AF',
            borderColor: '#374151',
            borderWidth: 1,
            callbacks: {
              label: (context: any) => {
                const value = context.parsed.y ?? 0;
                return `${context.dataset.label}: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#6B7280' }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              color: '#6B7280',
              callback: (value: any) => (Number(value) >= 0 ? '+' : '') + value + '%'
            }
          }
        }
      }
    });
  }

  getRecommendationTitle(signal: Signal): string {
    if (signal.signalType === 'BUY') {
      return 'BUY Signal';
    } else if (signal.signalType === 'SELL') {
      return 'SELL Signal';
    }
    return 'HOLD';
  }

  getRecommendationText(signal: Signal): string {
    if (signal.signalType === 'BUY') {
      return 'Technical indicators suggest a buying opportunity. Price may rise according to analysis.';
    } else if (signal.signalType === 'SELL') {
      return 'Technical indicators show weakness. Consider selling or avoid buying.';
    }
    return 'Technical indicators do not show a clear signal. Wait for more confirmation before acting.';
  }

getRecommendation(signalType: string): string {
    if (signalType === 'BUY') {
      return '✅ BUY - Technical signal positive. Price may rise.';
    } else if (signalType === 'SELL') {
      return '🔻 SELL - Technical signal negative. Price may fall.';
    }
return '⏳ HOLD - No clear signal. Wait for more confirmation.';
  }

  toggleReasonsExpanded(): void {
    this.reasonsExpanded = !this.reasonsExpanded;
  }

  getReasonCategory(reason: string): { color: string; label: string; type: string } {
    const lower = reason.toLowerCase();
    if (lower.includes('ema') || lower.includes('tendencia')) {
      return { color: '#22c55e', label: 'Trend', type: 'trend' };
    }
    if (lower.includes('rsi')) {
      return { color: '#f59e0b', label: 'RSI', type: 'rsi' };
    }
    if (lower.includes('macd')) {
      return { color: '#8b5cf6', label: 'MACD', type: 'macd' };
    }
    if (lower.includes('stoch')) {
      return { color: '#06b6d4', label: 'Stoch', type: 'stoch' };
    }
    return { color: '#94a3b8', label: 'Otros', type: 'other' };
  }

  getTrendIcon(trend: string): string {
    if (trend === 'ALCISTA') return '↑';
    if (trend === 'BAJISTA') return '↓';
    return '→';
  }

  getTrendClass(trend: string): string {
    if (trend === 'ALCISTA') return 'trend-up';
    if (trend === 'BAJISTA') return 'trend-down';
    return 'trend-neu';
  }

  getBadgeClass(signalType: string): string {
    if (signalType === 'BUY') return 'badge-buy';
    if (signalType === 'SELL') return 'badge-sell';
    return 'badge-hold';
  }

  getRelatedSignals(): Signal[] {
    if (!this.selectedSignal || this.signals.length <= 1) {
      return [];
    }
    const currentMarket = this.selectedSignal.market;
    const currentSymbol = this.selectedSignal.symbol;
    
    const differentMarket = this.signals
      .filter(s => s.symbol !== currentSymbol && s.market !== currentMarket)
      .slice(0, 4);
    
    if (differentMarket.length >= 4) {
      return differentMarket;
    }
    
    const remaining = this.signals
      .filter(s => s.symbol !== currentSymbol && !differentMarket.includes(s))
      .slice(0, 8 - differentMarket.length);
    
    return [...differentMarket, ...remaining];
  }

  onLogoError(event: Event): void {
    this.logoLoaded = false;
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
  }

  onTableLogoError(event: Event, signal: Signal): void {
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
  }

  onLogoLoad(): void {
    this.logoLoaded = true;
  }

}
