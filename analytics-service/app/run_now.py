import asyncio
import sys
import os

os.chdir("C:/Users/matia/OneDrive/Escritorio/app/analytics-service/app")
sys.path.insert(0, ".")

from services.data_fetcher import DataFetcher
from services.analyzer import TechnicalAnalyzer
from services.signal_generator import SignalGenerator
from services.scheduler import Scheduler

df = DataFetcher()
an = TechnicalAnalyzer()
sg = SignalGenerator()
scheduler = Scheduler(df, an, sg)

async def run():
    try:
        await scheduler.run_analysis()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(run())