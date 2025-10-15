import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
print('sys.path added:', sys.path[0])

try:
    import app
    print('imported app')
    import importlib
    importlib.invalidate_caches()
    import app.main
    print('imported app.main')
except Exception as e:
    import traceback
    print('ERROR during import:', type(e).__name__, e)
    traceback.print_exc()
