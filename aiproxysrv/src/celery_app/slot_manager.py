"""
Simple Slot Management für MUREKA API
"""
import sys
import time

# Global state - in Produktion sollte dies über Redis/DB laufen
current_requests = 0
active_tasks = {}


def acquire_mureka_slot(task_id: str) -> bool:
    """Versucht einen MUREKA Slot zu akquirieren"""
    global current_requests
    try:
        if current_requests >= 1:
            print(f"MUREKA slot not available for task {task_id} (current: {current_requests})", file=sys.stderr)
            return False
        current_requests += 1
        active_tasks[task_id] = time.time()
        print(f"MUREKA slot acquired for task {task_id} (current: {current_requests})", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error acquiring MUREKA slot for task {task_id}: {e}", file=sys.stderr)
        return False


def release_mureka_slot(task_id: str):
    """Gibt einen MUREKA Slot frei"""
    global current_requests
    try:
        if current_requests > 0:
            current_requests -= 1
        if task_id in active_tasks:
            del active_tasks[task_id]
        print(f"MUREKA slot released for task {task_id} (current: {current_requests})", file=sys.stderr)
    except Exception as e:
        print(f"Error releasing MUREKA slot for task {task_id}: {e}", file=sys.stderr)


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
