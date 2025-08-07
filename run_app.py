#!/usr/bin/env python3
"""
Climate Tech Funding Tracker - Application Runner
Easy way to start the Streamlit application
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the Streamlit application"""
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if virtual environment exists
    venv_path = project_dir / "venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found. Please run setup first.")
        print("Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements_basic.txt")
        return
    
    # Check if database is initialized
    db_path = project_dir / "data" / "funding_tracker.db"
    if not db_path.exists():
        print("🔧 Initializing database...")
        try:
            subprocess.run([
                str(venv_path / "bin" / "python"), 
                "src/init_db.py"
            ], check=True)
            print("✅ Database initialized successfully")
        except subprocess.CalledProcessError:
            print("❌ Database initialization failed")
            return
    
    print("🚀 Starting Climate Tech Funding Tracker...")
    print("📱 Open your browser to: http://localhost:8501")
    print("🔄 Use Ctrl+C to stop the application")
    print()
    
    try:
        # Run streamlit
        subprocess.run([
            str(venv_path / "bin" / "streamlit"),
            "run",
            "app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down Climate Tech Funding Tracker")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please ensure it's installed in your virtual environment.")
        print("Run: source venv/bin/activate && pip install -r requirements_basic.txt")

if __name__ == "__main__":
    main()