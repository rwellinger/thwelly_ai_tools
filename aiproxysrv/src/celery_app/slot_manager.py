"""
Simple Slot Management für MUREKA API
"""
import time
from utils.logger import logger

# Global state - in Produktion sollte dies über Redis/DB laufen
current_requests = 0
active_tasks = {}


def acquire_mureka_slot(task_id: str) -> bool:
    """Versucht einen MUREKA Slot zu akquirieren"""
    global current_requests
    try:
        if current_requests >= 1:
            logger.debug("MUREKA slot not available", extra={"task_id": task_id, "current_requests": current_requests})
            return False
        current_requests += 1
        active_tasks[task_id] = time.time()
        logger.info("MUREKA slot acquired", extra={"task_id": task_id, "current_requests": current_requests})
        return True
    except Exception as e:
        logger.error("Error acquiring MUREKA slot", extra={"task_id": task_id, "error": str(e)})
        return False


def release_mureka_slot(task_id: str):
    """Gibt einen MUREKA Slot frei"""
    global current_requests
    try:
        if current_requests > 0:
            current_requests -= 1
        if task_id in active_tasks:
            del active_tasks[task_id]
        logger.info("MUREKA slot released", extra={"task_id": task_id, "current_requests": current_requests})
    except Exception as e:
        logger.error("Error releasing MUREKA slot", extra={"task_id": task_id, "error": str(e)})


def wait_for_mureka_slot(task_id: str, max_wait: int = 3600) -> bool:
    """Wartet auf einen verfügbaren MUREKA Slot"""
    start_time = time.time()

    while time.time() - start_time < max_wait:
        if acquire_mureka_slot(task_id):
            return True
        time.sleep(10)
    return False


def get_slot_status() -> dict:
    """Gibt den aktuellen Slot-Status zurück"""
    return {
        "current_requests": current_requests,
        "max_concurrent": 1,
        "active_tasks": len(active_tasks),
        "available": current_requests < 1
    }
