
import importlib.util
import sys

print("Sys path:", sys.path)
try:
    spec = importlib.util.find_spec("homeassistant")
    print("Spec:", spec)
except Exception as e:
    print("Error finding spec:", e)

try:
    import homeassistant
    print("Imported:", homeassistant)
except ImportError as e:
    print("Import failed:", e)
