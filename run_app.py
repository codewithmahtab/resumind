#!/usr/bin/env python3
"""
Run script for Smart AI Resume Analyzer & Builder
College Final Year AIML Project
"""
import sys
import subprocess
import os

def main():
    print("========================================================")
    print("      Starting AI Resume Analyzer & Builder App")
    print("========================================================")
    
    app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_script])
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
