import asyncio
import sys
import os
import pandas as pd

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.external.cdc_wonder import CDCWonderClient

async def main():
    client = CDCWonderClient()
    try:
        print("Testing CDC WONDER (Birth Demographics)...")
        # Query for births by year
        df = await client.get_birth_demographics(year_range=["2021", "2022"], group_by=["Year"])
        if not df.empty:
            print("SUCCESS! Found CDC Data:")
            print(df.head())
        else:
            print("CDC returned empty data. Check connection or parameters.")
            
    except Exception as e:
        print(f"CDC ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
