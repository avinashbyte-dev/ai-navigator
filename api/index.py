import sys
import os
import shutil

# Resolve path to backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# On Vercel serverless functions, copy pre-seeded database to writable /tmp
if os.getenv("VERCEL"):
    tmp_db = "/tmp/ai_navigator.db"
    src_db = os.path.join(backend_dir, "ai_navigator.db")
    if not os.path.exists(tmp_db) and os.path.exists(src_db):
        try:
            shutil.copyfile(src_db, tmp_db)
        except Exception:
            pass

from main import app
