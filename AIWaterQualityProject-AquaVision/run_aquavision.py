"""AquaVision AI Water Quality Analysis Platform — Unified Server Launcher."""

import os
import sys
import webbrowser
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure Chatbot reference repo is on path
CHATBOT_DIR = BASE_DIR.parent / "AIWaterQualityProject-Chatbot"
if CHATBOT_DIR.exists() and str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

def main():
    print("=" * 72)
    print("   AQUAVISION - AI WATER QUALITY ANALYSIS & MONITORING PLATFORM")
    print("=" * 72)
    print(">>> Initializing unified server...")
    print(f">>> Backend Directory: {BACKEND_DIR}")
    print(f">>> Reference Chatbot Directory: {CHATBOT_DIR}")
    print(">>> Port: 8000")
    print(">>> Access URL: http://localhost:8000")
    print("=" * 72)

    import uvicorn
    # Change working directory to backend so relative paths work consistently
    os.chdir(str(BACKEND_DIR))
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()

