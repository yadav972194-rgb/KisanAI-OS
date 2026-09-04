"""
KisanAI OS Utility Module
Version: 1.0.0
"""

from datetime import datetime


def current_time():
    """Return current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def banner():
    print("=" * 50)
    print("🌾 KisanAI OS")
    print("AI Farming Assistant")
    print("=" * 50)


if __name__ == "__main__":
    banner()
    print("Current Time:", current_time())  