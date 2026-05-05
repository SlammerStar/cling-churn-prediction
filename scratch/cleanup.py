import os
files = ['api/__init__.py', 'ml/__init__.py', 'core/__init__.py', 'tests/__init__.py']
for f in files:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed {f}")
