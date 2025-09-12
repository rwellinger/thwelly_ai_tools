"""Song Account Controller - Handles MUREKA account operations"""
import sys
import requests
from typing import Tuple, Dict, Any
from config.settings import MUREKA_API_KEY, MUREKA_BILLING_URL


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

            print("Request URL", MUREKA_BILLING_URL)
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
            print(f"Request URL: {MUREKA_BILLING_URL}", file=sys.stderr)
            headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
            account_response = requests.get(MUREKA_BILLING_URL, headers=headers, timeout=10)

            if account_response.status_code == 200:
                account_data = account_response.json()
                balance = account_data.get("balance", 0)

                if balance <= 0:
                    print(f"Insufficient MUREKA balance: {balance}", file=sys.stderr)
                    return False
                else:
                    print(f"Account OK : {balance}", file=sys.stderr)
                    return True

        except Exception as e:
            print(f"Could not check MUREKA balance: {e}", file=sys.stderr)
            return False