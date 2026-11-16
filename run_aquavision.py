"""AquaVision AI Water Quality Analysis Platform — Unified Root Launcher."""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
AQUAVISION_DIR = ROOT_DIR / "AIWaterQualityProject-AquaVision"
BACKEND_DIR = AQUAVISION_DIR / "backend"
CHATBOT_DIR = ROOT_DIR / "AIWaterQualityProject-Chatbot"

for path_entry in [BACKEND_DIR, CHATBOT_DIR]:
    if path_entry.exists() and str(path_entry) not in sys.path:
        sys.path.insert(0, str(path_entry))

def main():
    print("=" * 72)
    print("   AQUAVISION - AI WATER QUALITY ANALYSIS & MONITORING PLATFORM")
    print("=" * 72)
    print(">>> Launching AquaVision...")
    print(f">>> Root Directory: {ROOT_DIR}")
    print(f">>> AquaVision Backend: {BACKEND_DIR}")
    print(">>> Access URL: http://localhost:8000")
    print("=" * 72)

    import uvicorn
    os.chdir(str(BACKEND_DIR))
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()

