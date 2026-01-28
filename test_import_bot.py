
import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.getcwd())

try:
    from src.trader.bot import MemeBot
    print("✅ Successfully imported MemeBot")
except Exception as e:
    print(f"❌ Failed to import MemeBot: {e}")
    import traceback
    traceback.print_exc()
