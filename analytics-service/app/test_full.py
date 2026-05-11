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

async def test_full():
    us, ar, eu, jp = await scheduler.fetch_stocks_from_api()
    print(f'US: {len(us)}, AR: {len(ar)}, EU: {len(eu)}, JP: {len(jp)}')
    
    signals = []
    # Test first 2 from each market
    for sym in us[:2]:
        result = await scheduler.analyze_symbol(sym, 'US')
        if result:
            signals.append(result)
            print(f'{sym}: {result["signal_type"]} (normalized: {result["normalized"]})')
        else:
            print(f'{sym}: FAILED')
    
    for sym in ar[:2]:
        result = await scheduler.analyze_symbol(sym, 'AR')
        if result:
            signals.append(result)
            print(f'{sym}: {result["signal_type"]} (normalized: {result["normalized"]})')
        else:
            print(f'{sym}: FAILED')
    
    for sym in eu[:2]:
        result = await scheduler.analyze_symbol(sym, 'EU')
        if result:
            signals.append(result)
            print(f'{sym}: {result["signal_type"]} (normalized: {result["normalized"]})')
        else:
            print(f'{sym}: FAILED')

    for sym in jp[:2]:
        result = await scheduler.analyze_symbol(sym, 'JP')
        if result:
            signals.append(result)
            print(f'{sym}: {result["signal_type"]} (normalized: {result["normalized"]})')
        else:
            print(f'{sym}: FAILED')
    
    print(f'\nTotal signals: {len(signals)}')
    
    if signals:
        print('Sending to API...')
        result = await sg.send_signals_to_api(signals)
        print(f'API result: {result}')
    
    print('DONE')

asyncio.run(test_full())
