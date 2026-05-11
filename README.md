# QuantEdge - Automatic Stock Analysis System

## Overview

QuantEdge is an automated stock analysis system that generates trading signals (BUY, SELL, HOLD) based on technical indicators. It monitors stocks across multiple markets (US, AR, EU, JP) and provides real-time signals through a web dashboard.

Data is sourced from **Yahoo Finance (YFinance API)** for price data and technical indicators.

---

## Architecture

```
                                    ┌─────────────────┐
                                    │   YFINANCE      │
                                    │   (Data API)     │
                                    └────────┬────────┘
                                             │ price data
                                             ↓
┌─────────────────┐                         ┌─────────────────┐    REST API    ┌─────────────────┐
│   PYTHON        │ ──POST /api/signals─────→│   JAVA          │────────────────→│   ANGULAR       │
│   Analytics     │                         │   Spring Boot   │                 │   Frontend      │
│   (FastAPI)     │                         │   (API)         │                 │   (Dashboard)   │
└─────────────────┘                         └────────┬────────┘                     └─────────────────┘
                                                   │                                    │
                                                   ↓                                    │
                                             ┌─────────────────┐                      │
                                             │   PostgreSQL    │◄─────────────────────┘
                                             │   (stockanalyzer)│   serves history, signals
                                             └─────────────────┘
```

**Data flow:**
- Python fetches stock data from YFinance → calculates indicators → sends signals to Java API
- Java API stores signals and historical data in PostgreSQL
- Angular fetches signals and history from Java API (not from Python)

---

## Production URLs

| Service | URL |
|---------|-----|
| **Frontend (Dashboard)** | https://quant-edge-app-lime.vercel.app |
| **Backend API** | https://quantedge-api-a1ib.onrender.com |

---

## Quick Start (Local Development)

### 1. Setup Database
```bash
# Install PostgreSQL 14+
# Create database:
psql -U postgres -c "CREATE DATABASE stockanalyzer;"
```

### 2. Start Java API
```bash
cd api-service
mvn spring-boot:run
# Runs at http://localhost:8081
```

### 3. Start Python Analytics Service
```bash
cd analytics-service
pip install -r requirements.txt
cd app
python main.py
# Runs at http://localhost:8000
```

### 4. Start Frontend
```bash
cd frontend
npm install
ng serve
# Runs at http://localhost:4200
```

---

## Requirements

- Java 17+
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+

---

## Python Service (Analytics)

### Installation

```bash
cd analytics-service
pip install -r requirements.txt
```

**Note:** TA-Lib requires manual installation. Download from: https://ta-lib.org/

### Execution

```bash
cd analytics-service/app
python main.py
```

The service will run at `http://localhost:8000`

### Endpoints

- `GET /` - Service status
- `GET /health` - Health check
- `POST /analyze` - Analyze stocks
- `POST /scheduler/start` - Start scheduler

### Configuration

Edit `.env`:
```
API_URL=http://localhost:8081
```

---

## Java Service (API)

### Compilation

```bash
cd api-service
mvn clean install
```

### Execution

```bash
cd api-service
mvn spring-boot:run
```

The API will run at `http://localhost:8081`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/signals/today | Today's signals |
| GET | /api/signals | Paginated signals |
| GET | /api/signals/history | Signal history (paginated) |
| GET | /api/signals/{symbol} | Latest signal by symbol |
| POST | /api/signals/batch | Receive signals in batch (from Python) |
| POST | /api/signals | Receive individual signal (from Python) |
| DELETE | /api/signals/today | Delete today's signals |
| GET | /api/health | Health check |
| GET | /api/stocks/{symbol}/history | Stock historical data (price, indicators) |
| GET | /api/stocks/{symbol}/seasonality | Seasonal performance data |
| POST | /api/stocks/{symbol}/history/batch | Internal — called by Python batch only |

**Note:** This API does not require authentication to access its endpoints.

---

## Angular Frontend

### Installation

```bash
cd frontend
npm install
```

### Execution

```bash
ng serve
```

The frontend will run at `http://localhost:4200`

**Note:** The frontend currently has no login functionality since the API does not require authentication.

---

## Scheduled Jobs (GitHub Actions)

### Daily Analysis Workflow

The Python analytics service is triggered automatically via GitHub Actions.

- **Location**: `.github/workflows/daily-analysis.yml`
- **Schedule**: Automatic, Monday-Friday at 9:00 AM UTC (6:00 AM Argentina)
- **Manual trigger**: Available via GitHub Actions UI

**What it does:**
1. Installs Python dependencies
2. Runs the analysis service
3. Fetches stock data from Yahoo Finance
4. Calculates technical indicators (RSI, MACD, EMA, etc.)
5. Generates trading signals
6. Sends signals to the Java API
7. Verifies signals were saved successfully

### If the workflow doesn't run automatically:

1. **Manual trigger**: Go to GitHub Actions → `Daily Stock Analysis` → Run workflow
2. **Check schedule**: Cron is set to `0 9 * * 1-5` (9 AM UTC, Mon-Fri)
3. **Verify secrets**: Ensure `API_URL` is configured in repo Settings → Secrets
4. **Check GitHub Actions logs**: Any errors will be visible in the workflow run

---

## Data Source

- **Yahoo Finance (YFinance API)**: Real-time stock prices and historical data
- **Technical indicators**: RSI, MACD, EMA (20/50), Bollinger Bands, Stochastic, ATR, ADX
- **Markets covered**: US, Argentina (AR), Europe (EU), Japan (JP)

---

## Monitored Stocks

### USA
AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, NFLX, INTC, JNJ, JPM, KO, LLY, LYFT, MA, MCD, MRK, MSFT, NIO, NKE, NVDA, ORCL, PEP, PFE, PLTR, PYPL, RIVN, ROKU, SLB, SNAP, SNOW, T, TSLA, UBER, UNH, V, VZ, WFC, WMT, XOM, XPEV, ZS

### Argentina
GGAL, YPF, PAMP, SUPV, CEPU

### Europe
AIR.PA, ALV.DE, ASML.AS, DTE.DE, NESN.SW, OR.PA, SAP.DE, SHEL.L

### Japan
SONY, TM

---

## Signal Algorithm

### Overview

The signal generation uses a multi-factor scoring system that normalizes to **-1.0 to +1.0**, then converts to **0-100** for final signal classification.

### Scoring Factors (10 indicators)

| # | Factor | Weight | Condition |
|---|-------|--------|-----------|
| 1 | **ADX Filter** | 0 | ADX < threshold: penalty applied, still evaluates all factors |
| 2 | **Trend (EMA20/EMA50)** | `trend_weight` (2) | EMA20 > EMA50: +weight / EMA20 < EMA50: -weight |
| 3 | **RSI** | `rsi_reversal_weight` (3) | RSI < 30: +weight / RSI > 70: -weight |
| 4 | **MACD Crossover** | `macd_cross_weight` (2) | Bullish cross: +weight / Bearish cross: -weight |
| 5 | **Stochastic %K/%D** | 1.0 | %K < 20: +1.0 / %K > 80: -1.0 / Bull cross: +0.75 |
| 6 | **Bollinger Bands** | 0.5 | Price at lower band: +0.5 / upper band: -0.5 |
| 7 | **Support/Resistance** | 0.5 | Near 52w low + bullish: +0.5 / Near 52w high + bearish: -0.5 |
| 8 | **Volume Relative** | `volume_weight` (1) | Vol ≥ 1.5x avg: ±weight / Vol ≤ 0.5x: score ×0.8 |
| 9 | **ATR Volatility** | `atr_penalty` (0.5) | ATR% > threshold: score ×(1-penalty) |
| 10 | **Normalization** | - | raw_score / max_possible → -1/+1 → 0-100 |

### Signal Classification

| Normalized Score | Signal | Color |
|------------------|-------|-------|
| ≥ `buy_threshold` (0.30) | **BUY** | Green |
| ≤ `-sell_threshold` (-0.30) | **SELL** | Red |
| Between -0.30 and +0.30 | **HOLD** | Gray |

### Market-Specific Configurations

Different thresholds per market (configured in `config/stock-config.json`):

| Market | RSI Oversold | RSI Overbought | ATR High | ADX Min | Vol Multiplier |
|--------|---------------|----------------|----------|---------|----------------|
| **US** | 30 | 70 | 3% | 20 | 1.5x |
| **AR** | 35 | 65 | 5% | 25 | 2.0x |
| **EU** | 30 | 70 | 2.5% | 20 | 1.5x |
| **JP** | 30 | 70 | 2% | 20 | 1.5x |

### Example Calculation

```
Stock: AAPL (US market)
- Trend: EMA20 > EMA50 → +2.0
- RSI: 28 (< 30) → +3.0
- MACD: Bullish crossover → +2.0
- Volume: 2.1x average → +1.0
- ATR: 1.5% (< 3%) → no penalty

Raw Score: +8.0 / Max Possible: 10.0 = 0.80 normalized
Final Score: (0.80 + 1) / 2 × 100 = 90 → BUY
```

---

## Testing

### Python Service (Analytics) Tests

**Location:** `analytics-service/app/tests/`

**Test Configuration:** `analytics-service/pytest.ini`

**Test Files:**
- `tests/unit/test_analyzer.py` - Analyzer tests
- `tests/unit/test_signal_generator.py` - Signal generator tests
- `tests/unit/test_company_metadata.py` - Company metadata tests
- `tests/unit/test_data_fetcher.py` - Data fetcher tests
- `tests/unit/test_scheduler.py` - Scheduler tests

**Run all tests:**
```bash
cd analytics-service
pytest
```

**Run with verbose output:**
```bash
cd analytics-service
pytest -v
```

---

### Java Service (API) Tests

**Location:** `api-service/src/test/`

**Test Files:**
- `src/test/java/com/stockanalyzer/service/impl/SignalServiceImplTest.java`
- `src/test/java/com/stockanalyzer/service/impl/StockServiceImplTest.java`
- `src/test/java/com/stockanalyzer/controller/SignalControllerTest.java`
- `src/test/java/com/stockanalyzer/controller/StockControllerTest.java`
- `src/test/java/com/stockanalyzer/exception/GlobalExceptionHandlerTest.java`

**Run all tests:**
```bash
cd api-service
mvn test
```

**Run specific test class:**
```bash
cd api-service
mvn test -Dtest=SignalServiceImplTest
```

**Run specific test method:**
```bash
cd api-service
mvn test -Dtest=SignalServiceImplTest#methodName
```

---

### Angular Frontend Tests

**Location:** `frontend/src/`

**Test Files:**
- `src/app/components/dashboard/dashboard.component.spec.ts`
- `src/app/services/signal.service.spec.ts`

**Run tests:**
```bash
cd frontend
npm test
```

**Run tests with coverage:**
```bash
cd frontend
npm test -- --code-coverage
```

---

## Troubleshooting

### Python Service won't start
- Ensure Python 3.9+ is installed
- Check TA-Lib is installed correctly
- Verify `PYTHONPATH` includes the app directory

### Java API returns 500 error
- Check PostgreSQL is running and accessible
- Verify `application.properties` has correct credentials
- Ensure database `stockanalyzer` exists

### Frontend can't connect to API
- Verify Java API is running on port 8081
- Check `environment.ts` has correct `apiUrl`
- For production: ensure Vercel can reach Render API

### GitHub Actions workflow not running
- Go to Actions → `Daily Stock Analysis` → Run workflow manually
- Check repo Settings → Secrets: `API_URL` must be configured
- Review workflow logs for errors
- Verify cron schedule: `0 9 * * 1-5` (Mon-Fri at 9 AM UTC)

---

## License

MIT