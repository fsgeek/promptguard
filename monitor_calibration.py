"""Monitor calibration progress."""
import json
import time
from pathlib import Path
from datetime import datetime

def monitor():
    """Monitor calibration progress."""
    raw_file = Path("diversity_calibration_raw.json")

    while True:
        if raw_file.exists():
            try:
                with open(raw_file) as f:
                    data = json.load(f)

                completed = len(data.get("results", []))
                total = data.get("total_prompts", 478)
                pct = (completed / total * 100) if total > 0 else 0

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {completed}/{total} ({pct:.1f}%)")

                if completed >= total:
                    print("\n✅ Calibration complete!")
                    break

            except json.JSONDecodeError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] File being written...")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for output file...")

        time.sleep(30)

if __name__ == "__main__":
    monitor()
