
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from fastapi import FastAPI
from backend.main import app

# print("--- REGISTRY ---")
for route in app.routes:
    path = route.path
    methods = getattr(route, "methods", "None")
    print(str(path) + " " + str(methods))
