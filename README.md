# Stock Analyzer - Automatic Stock Analysis System

## Architecture

```
┌─────────────────┐    POST /api/signals    ┌─────────────────┐    REST API    ┌─────────────────┐
│   PYTHON        │ ──────────────────────→  │   JAVA          │ ─────────────→ │   ANGULAR       │
│   Analytics     │                         │   Spring Boot   │                 │   Frontend      │
│   (FastAPI)     │ ←─────────────────────  │   (API)         │ ←─────────────  │   (Dashboard)   │
└─────────────────┘             │            └─────────────────┘                     └─────────────────┘
        │                       │                                 │
        │         PostgreSQL (localhost:5432)       │
        │         Database: stockanalyzer           │
        └────────────────┬──────────────────────────┘
```

---

## Requirements

- Java 17+
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+

---

## Database Configuration

### PostgreSQL

1. Install PostgreSQL
2. Create the database:

```sql
CREATE DATABASE stockanalyzer;
```

3. Credentials configured in `api-service/src/main/resources/application.properties`:
   - User: postgres
   - Password: 1234

---

## 1. Python Service (Analytics)

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

## 2. Java Service (API)

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

**Note:** This API does not require authentication to access its endpoints.

---

## 3. Angular Frontend

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

## Complete Execution

1. **Start PostgreSQL** and create the `stockanalyzer` database

2. **Start Java API**:
   ```bash
   cd api-service
   mvn spring-boot:run
   ```

3. **Start Python Analytics**:
   ```bash
   cd analytics-service/app
   python main.py
   ```

4. **Start Frontend**:
   ```bash
   cd frontend
   ng serve
   ```

5. **Open browser**: http://localhost:4200

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

## Monitored Stocks

### USA
AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, NFLX

### Argentina
GGAL, BYMA, YPF, PAMP, SUPV, CEPU

---

## Signal Algorithm

### Overview
The signal generation uses a multi-factor scoring system that normalizes to **-1.0 to +1.0**, then converts to **0-100** for final signal classification.

### Scoring Factors (10 indicators)

| # | Factor | Weight | Condition |
|---|-------|--------|-----------|
| 1 | **ADX Filter** | - | ADX < threshold → HOLD (no trend) |
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
| ≥ `buy_threshold` (0.30) | **BUY** 🟢 | Green |
| ≤ `-sell_threshold` (-0.30) | **SELL** 🔴 | Red |
| Between -0.30 and +0.30 | **HOLD** ⚪ | Gray |

### Market-Specific Configurations

Different thresholds per market (configured in `config/stock-config.json`):

| Market | RSI Oversold | RSI Overbought | ATR High | ADX Min | Vol Multiplier |
|--------|---------------|----------------|----------|---------|-----------------|
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
Final Score: (0.80 + 1) / 2 × 100 = 90 → BUY 🟢
```

---

## License

MIT
