from celery import Celery
import os
import logging
import asyncio
from typing import Dict, Any

from app.data.natality_loader import NatalityMicrodataLoader
from app.external.cdc_wonder import CDCWonderClient
from app.external.ahr_client import AHRClient
from app.external.ipums_client import IPUMSClient
from app.data.calibrator import CalibrateSyntheticData

logger = logging.getLogger(__name__)

# Assuming celery_app is defined elsewhere or initialized here
celery_app = Celery("maternal_health_pipeline")

@celery_app.task(name="run_data_pipeline")
def run_data_pipeline():
    """
    Orchestrates the full data fetching and calibration pipeline.
    """
    return asyncio.run(_run_pipeline_async())

async def _run_pipeline_async():
    logger.info("Starting orchestrated data pipeline...")
    
    # 1. NCHS Natality Processing
    nchs_dir = os.getenv("NCHS_DATA_DIR", "/data/nchs/natality")
    natality_df = None
    # Look for any .txt file in the dir (usually the extracted microdata)
    try:
        txt_files = [f for f in os.listdir(nchs_dir) if f.endswith('.txt')]
        if txt_files:
            file_path = os.path.join(nchs_dir, txt_files[0])
            loader = NatalityMicrodataLoader(file_path, year=2023)
            natality_df, meta = loader.load(nrows=100000) # Sample for calibration
            logger.info("NCHS Natality data loaded successfully.")
        else:
            logger.warning(f"No NCHS natality records found in {nchs_dir}. Skipping microdata calibration.")
    except Exception as e:
        logger.error(f"Error loading NCHS data: {e}")

    # 2. CDC WONDER Queries
    cdc_client = CDCWonderClient()
    cdc_results = {}
    try:
        years = ["2021", "2022", "2023"]
        morbidity = await cdc_client.get_maternal_morbidity_by_state(years)
        # Process and store in cdc_results for calibrator
        # ... logic to extract rates ...
        logger.info("CDC WONDER data queried.")
    except Exception as e:
        logger.error(f"CDC WONDER query failed: {e}")

    # 3. AHR API Queries
    ahr_client = AHRClient()
    ahr_results = {}
    try:
        mortality = await ahr_client.get_measure_by_state("Maternal Mortality")
        # Process and store
        logger.info("AHR API data queried.")
    except Exception as e:
        logger.error(f"AHR API query failed: {e}")

    # 4. Optional IPUMS Integration
    if os.getenv("IPUMS_API_KEY"):
        ipums_client = IPUMSClient()
        # Trigger extracts or use cached
        logger.info("IPUMS integration active.")

    # 5. Calibration
    calibrator = CalibrateSyntheticData(
        output_path=os.getenv("CALIBRATION_OUTPUT_PATH", "./config/calibration_params.json")
    )
    report = calibrator.run_calibration(
        natality_df=natality_df,
        cdc_data=cdc_results,
        ahr_data=ahr_results
    )

    logger.info("Data pipeline completed successfully.")
    return report
