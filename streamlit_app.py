"""
Streamlit Community Cloud Root Entrypoint

Provides a standard entrypoint for Streamlit Cloud deployments, ensuring
the dashboard runs correctly regardless of whether the deploy settings specify
'streamlit_app.py' or 'frontend/app.py'.
"""

import sys
from pathlib import Path

# Ensure repository root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Execute frontend application
frontend_app = ROOT_DIR / "frontend" / "app.py"
with open(frontend_app, "r", encoding="utf-8") as f:
    code = compile(f.read(), str(frontend_app), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(frontend_app)})
