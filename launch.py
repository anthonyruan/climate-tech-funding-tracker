#!/usr/bin/env python3
"""
Launch script for Climate Tech Funding Tracker
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the Climate Tech Funding Tracker"""
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🌱 Climate Tech Funding Tracker")
    print("=" * 50)
    print("🚀 Starting application...")
    
    # Check if virtual environment exists
    venv_path = project_dir / "venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("💡 Please run setup first:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print("   pip install -r requirements_basic.txt")
        return 1
    
    try:
        # Use the launcher script if available
        if (project_dir / "run_app.py").exists():
            cmd = [sys.executable, "run_app.py"]
        else:
            # Fallback to direct streamlit
            if sys.platform.startswith('win'):
                streamlit_path = venv_path / "Scripts" / "streamlit.exe"
            else:
                streamlit_path = venv_path / "bin" / "streamlit"
            
            cmd = [str(streamlit_path), "run", "app.py"]
        
        print(f"🔗 Application will be available at: http://localhost:8501")
        print("⚡ Starting server...")
        print()
        
        # Start the application
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        return 1
    except FileNotFoundError:
        print("❌ Streamlit not found!")
        print("💡 Please install dependencies: pip install -r requirements_basic.txt")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())