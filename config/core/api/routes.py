"""
KisanAI OS
API Routes
Version: 2.0.0
"""

ROUTES = {
    "farmer": "/api/farmers",
    "crop": "/api/crops",
    "soil": "/api/soils",
    "weather": "/api/weather",
    "disease": "/api/diseases",
}


if __name__ == "__main__":

    print("=" * 50)
    print("KisanAI API Routes Loaded Successfully")
    print("=" * 50)

    for name, route in ROUTES.items():
        print(f"{name} -> {route}")