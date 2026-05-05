import sys
import os
try:
    from local_app import app
    print("Success: local_app imported")
except ImportError as e:
    print(f"Error: {e}")
    print(f"Path: {sys.path}")
