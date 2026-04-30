# QuantEdge - Agent Guidelines

This document provides guidelines for agents working on the QuantEdge stock analysis application.

## Best Practices Documents

Agents MUST follow these best practice guides when working on the codebase:

| Document | When to Use |
|----------|-------------|
| `ANGULAR_BEST_PRACTICES.md` | Angular/TypeScript development |
| `JAVA_SPRING_BOOT_BEST_PRACTICES.md` | Java/Spring Boot API development |
| `FRONTEND_UX_UI_BEST_PRACTICES.md` | UI/UX, styling, CSS, accessibility |

---

## Project Overview

QuantEdge is a multi-service stock analysis application consisting of:
- **analytics-service** (Python/FastAPI) - Data fetching and technical analysis
- **api-service** (Java/Spring Boot) - REST API and database
- **frontend** (Angular 18) - Dashboard UI

## Architecture

```
[Python Analytics] --> [Java API] --> [PostgreSQL]
                           |
                           v
                    [Angular Frontend]
```

---

## Build & Run Commands

### Python Analytics Service (Port 8000)

```bash
# Install dependencies
pip install -r analytics-service/requirements.txt

# Run service
cd analytics-service/app
python3 main.py

# Run analysis manually
curl -X POST http://localhost:8000/analyze/run
```

### Java API Service (Port 8081)

```bash
# Build
cd api-service && mvn clean package

# Run
cd api-service && mvn spring-boot:run

# Compile only
cd api-service && mvn compile

# Run tests
cd api-service && mvn test

# Run single test class
cd api-service && mvn test -Dtest=SignalServiceTest

# Run single test method
cd api-service && mvn test -Dtest=SignalServiceTest#testMethodName
```

### Angular Frontend (Port 4200)

```bash
# Install dependencies
cd frontend && npm install

# Run development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Run tests with coverage
npm test -- --code-coverage
```

---

## Code Style Guidelines

### Python (analytics-service)

**Formatting:**
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use Black for formatting if available

**Imports:**
- Standard library first, then third-party, then local
- Group: stdlib > third-party > local
- Example:
```python
import os
from datetime import datetime

import httpx
import pandas as pd

from services.data_fetcher import DataFetcher
from services.analyzer import TechnicalAnalyzer
```

**Naming:**
- Classes: `PascalCase` (e.g., `SignalGenerator`)
- Functions/methods: `snake_case` (e.g., `generate_signal`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_URL`)
- Private methods: prefix with `_` (e.g., `_create_explanation`)

**Type Hints:**
- Use type hints for function parameters and return types
- Example: `def generate_signal(self, indicators: dict, price: float, volume: float = 0) -> dict:`

**Error Handling:**
- Use try/except with specific exception types
- Always log errors with context
- Example:
```python
try:
    df = data_fetcher.fetch_data(symbol, market)
    if df is None or df.empty:
        continue
except Exception as e:
    print(f"Error analyzing {symbol}: {e}")
    continue
```

---

### Java (api-service)

**Formatting:**
- Use Google Java Format or standard IntelliJ formatting
- 4 spaces for indentation
- Maximum line length: 120 characters

**Imports:**
- Group: static imports > java > javax > third-party > project
- Do not use wildcard imports (`import java.util.*`)
- Example:
```java
import com.stockanalyzer.dto.SignalDTO;
import com.stockanalyzer.model.Signal;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Service;
```

**Naming:**
- Classes/Interfaces: `PascalCase` (e.g., `SignalService`)
- Methods: `camelCase` (e.g., `getTodaySignals`)
- Constants: `UPPER_SNAKE_CASE`
- Variables: `camelCase` (e.g., `signalRepository`)

**Annotations:**
- Use Lombok `@Data`, `@NoArgsConstructor`, `@AllArgsConstructor` for DTOs
- Use `@Service` for service classes
- Use `@RestController` for controllers
- Use `@Transactional` for write operations

**Dependency Injection:**
- Constructor injection preferred (used throughout this codebase)
```java
private final SignalRepository signalRepository;
private final StockService stockService;

public SignalService(SignalRepository signalRepository, StockService stockService) {
    this.signalRepository = signalRepository;
    this.stockService = stockService;
}
```

**Error Handling:**
- Use proper HTTP status codes in controllers
- Return `ResponseEntity` for flexible responses
- Example:
```java
@GetMapping("/{symbol}")
public ResponseEntity<Stock> getStock(@PathVariable String symbol) {
    return stockService.getStockBySymbol(symbol)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
}
```

---

### TypeScript/Angular (frontend)

**Formatting:**
- Use ESLint and Prettier
- 2 spaces for indentation
- Maximum line length: 100 characters

**Imports:**
- Group: Angular > third-party > local
- Use absolute imports from `@app/` when possible
- Example:
```typescript
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SignalService } from '../../services/signal.service';
import { Signal } from '../../models/stock.model';
```

**Naming:**
- Components: `PascalCase` with `.component` suffix (e.g., `DashboardComponent`)
- Services: `PascalCase` with `.service` suffix (e.g., `SignalService`)
- Interfaces: `PascalCase` (e.g., `Signal`)
- Methods/variables: `camelCase`

**Component Structure:**
- Use standalone components
- Include all decorators, template, and styles in one file for simple components
- Use OnInit for initialization logic

**Templates:**
- Use strict typing in templates
- Prefer `*ngIf` and `*ngFor` structural directives
- Use async pipe for observables

---

## Testing Guidelines

### Python
- Use pytest if available
- Create tests in `tests/` directory
- Example: Test the signal generation logic

### Java
- Use JUnit 5 (Jupiter)
- Create tests in `src/test/java/`
- Follow naming: `ClassNameTest`
- Example:
```java
@SpringBootTest
class SignalServiceTest {
    @Autowired
    private SignalService signalService;
    
    @Test
    void testGetTodaySignals() {
        // test implementation
    }
}
```

### Angular
- Use Jasmine/Karma (default)
- Create tests in `.spec.ts` files
- Example:
```typescript
describe('DashboardComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardComponent]
    }).compileComponents();
  });
});
```

---

## Database

- PostgreSQL is used for persistence
- JPA/Hibernate for ORM in Java
- Entities are in `api-service/src/main/java/com/stockanalyzer/model/`
- Repositories are in `api-service/src/main/java/com/stockanalyzer/repository/`

---

## Common Tasks

### Restarting Services
After code changes in each service, restart:

1. **Python**: Kill process on port 8000, then `cd analytics-service/app && python3 main.py`
2. **Java**: Kill process on port 8081, then `cd api-service && mvn spring-boot:run`
3. **Frontend**: `npm run build` (automatically updates if using ng serve)

### Running Full Analysis
```bash
curl -X POST http://localhost:8000/analyze/run
```

### Checking Service Health
- Python: `curl http://localhost:8000/health`
- Java: `curl http://localhost:8081/api/signals/today`

---

## Notes

- The Python service fetches stock data from Yahoo Finance (yfinance)
- Technical indicators: RSI (14), EMA (20, 50), MACD (12, 26, 9), ATR (14)
- Signal scoring: -2 to +6 scale with trend, RSI, and MACD factors
- The frontend dashboard shows signals with company names and trend indicators

---

## Quick Reference

### Angular Development
- Use standalone components
- Follow `ANGULAR_BEST_PRACTICES.md` for component structure
- Use `@app/` absolute imports
- Always unsubscribe from observables (use `takeUntilDestroyed()` or `takeUntil()`)

### Java/Spring Boot
- Use constructor injection (no `@Autowired` fields)
- Follow `JAVA_SPRING_BOOT_BEST_PRACTICES.md` for service patterns
- Use `@Transactional(readOnly = true)` for read operations
- Keep DTOs separate from entities

### Frontend UX/UI
- Follow `FRONTEND_UX_UI_BEST_PRACTICES.md` for styling
- Use CSS custom properties for theming
- Ensure WCAG 2.1 accessibility compliance
- Mobile-first responsive design
