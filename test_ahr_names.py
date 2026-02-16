import asyncio
import sys
import os

# Add the project root to sys.path so we can import app
sys.path.append(os.getcwd())

from app.external.ahr_client import AHRClient

async def main():
    client = AHRClient()
    try:
        # Fetch some measure names to see what they are actually called
        query = "query { data_A(limit: 50) { measure { name } } }"
        results = await client._execute_query(query)
        measures = sorted(list(set(r.measure.name for r in results)))
        print("FOUND MEASURES:")
        for m in measures:
            print(f" - {m}")
            
        # specifically check for maternal measures
        maternal_query = "query { data_A(where: { measure: { name: { contains: \"Maternal\" } } }) { measure { name } } }"
        results = await client._execute_query(maternal_query)
        maternal_measures = sorted(list(set(r.measure.name for r in results)))
        print("\nMATERNAL MEASURES:")
        for m in maternal_measures:
            print(f" - {m}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
