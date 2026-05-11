import asyncio
import os
import sys

os.environ['FINNHUB_API_KEY'] = 'd76jvg9r01qtg3ndsrpgd76jvg9r01qtg3ndsrq0'
sys.path.insert(0, '.')

from services.data_fetcher import DataFetcher
from services.analyzer import TechnicalAnalyzer
from services.signal_generator import SignalGenerator
from services.scheduler import Scheduler

df = DataFetcher()
an = TechnicalAnalyzer()
sg = SignalGenerator()
scheduler = Scheduler(df, an, sg)

async def test():
    us, ar, eu, jp = await scheduler.fetch_stocks_from_api()
    print(f'US: {len(us)}, AR: {len(ar)}, EU: {len(eu)}, JP: {len(jp)}')
    
    result = await scheduler.analyze_symbol('AAPL', 'US')
    if result:
        print(f'AAPL: {result["signal_type"]}')
    else:
        print('AAPL: FAILED')
    
    print('DONE')

asyncio.run(test())
