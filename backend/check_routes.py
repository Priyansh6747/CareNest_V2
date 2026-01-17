import sys
import os

# Add backend directory to sys.path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

with open("routes.txt", "w") as f:
    for route in app.routes:
        if hasattr(route, "path"):
            f.write(f"{route.methods} {route.path}\n")
        else:
            f.write(f"Mounted: {route.path}\n")
