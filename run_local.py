import subprocess
import os
import sys

def run_local():
    print("🚀 MusicX Local Scraper Helper")
    print("-------------------------------")
    
    # Check if we are in the right directory
    if not os.path.exists('server.py'):
        print("❌ Error: server.py not found. Please run this script from the scraper_service directory.")
        return

    # Install requirements if needed
    print("📦 Checking dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    print("\n✅ Dependencies ready.")
    print("🌐 Starting scraper at http://localhost:5001")
    print("💡 Note: If using Android Emulator, the app will automatically find this via 10.0.2.2")
    print("-------------------------------\n")

    # Run the server
    try:
        subprocess.run([sys.executable, "server.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Local scraper stopped.")

if __name__ == "__main__":
    run_local()
