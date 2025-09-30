"""Song Account Controller - Handles MUREKA account operations"""
import requests
from typing import Tuple, Dict, Any
from config.settings import MUREKA_API_KEY, MUREKA_BILLING_URL
from utils.logger import logger


class SongAccountController:
    """Controller for MUREKA account operations"""
    
    def get_mureka_account(self) -> Tuple[Dict[str, Any], int]:
        """Get MUREKA Account Information"""
        if not MUREKA_API_KEY:
            return {"error": "MUREKA_API_KEY not configured"}, 500

        try:
            headers = {
                "Authorization": f"Bearer {MUREKA_API_KEY}"
            }

            logger.debug("Fetching MUREKA account info", url=MUREKA_BILLING_URL)
            response = requests.get(MUREKA_BILLING_URL, headers=headers, timeout=10)
            response.raise_for_status()

            account_data = response.json()
            return {
                "status": "success",
                "account_info": account_data
            }, 200

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Failed to fetch MUREKA account info: {str(e)}"
            }, 500
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }, 500
    
    def check_balance(self) -> bool:
        """Check Balance"""
        try:
            logger.debug("Checking MUREKA balance", url=MUREKA_BILLING_URL)
            headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
            account_response = requests.get(MUREKA_BILLING_URL, headers=headers, timeout=10)

            if account_response.status_code == 200:
                account_data = account_response.json()
                balance = account_data.get("balance", 0)

                if balance <= 0:
                    logger.warning("Insufficient MUREKA balance", balance=balance)
                    return False
                else:
                    logger.info("MUREKA account OK", balance=balance)
                    return True

        except Exception as e:
            logger.error("Could not check MUREKA balance", error=str(e))
            return False