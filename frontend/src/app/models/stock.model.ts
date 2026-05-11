export interface Signal {
  id?: number;
  symbol: string;
  companyName: string;
  market: string;
  signalType: string;
  rsi: number;
  ema20: number;
  ema50: number;
  macd: number;
  atr: number;
  price: number;
  priceChange24h: number;
  priceChangePercent24h: number;
  volumeRelative?: number;
  trend: string;
  explanation: string;
  summary?: string;
  reasons?: string[];
  analyzedAt: string;
  sector?: string;
  industry?: string;
  exchange?: string;
  country?: string;
  logoUrl?: string;
  marketCap?: number;
}

export interface Stock {
  id: number;
  symbol: string;
  name?: string;
  market: string;
  createdAt: string;
  updatedAt: string;
}

export interface LoginResponse {
  token: string;
}

export interface PageResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
  last: boolean;
  first: boolean;
}

export interface SignalGenerated {
  date: string;
  atPrice: number;
  rsi: number;
  type: string;
}

export interface ChartData {
  dates: string[];
  price: number[];
  ema20: number[];
  ema50: number[];
  rsi: number[];
}

export interface StockHistory {
  symbol: string;
  companyName: string;
  logoUrl?: string;
  market: string;
  signalType: string;
  currentPrice: number;
  priceChange24h: number;
  priceChangePercent24h: number;
  high52w: number;
  low52w: number;
  signalGenerated: SignalGenerated;
  chartData: ChartData;
  cachedAt?: string;
  cacheExpiresAt?: string;
  sector?: string;
  industry?: string;
  exchange?: string;
  country?: string;
  marketCap?: number;
  adx?: number;
  plusDi?: number;
  minusDi?: number;
  bbUpper?: number;
  bbMiddle?: number;
  bbLower?: number;
  stochK?: number;
  stochD?: number;
  srPosition?: number;
  macdLine?: number;
  macdSignal?: number;
  seasonality?: Seasonality;
}

export interface Seasonality {
  years: string[];
  yearlyReturns: { [key: string]: number[] };
  monthlyAvg: number[];
  months: string[];
  bestMonth: string | null;
  worstMonth: string | null;
  avgReturn: number;
}
