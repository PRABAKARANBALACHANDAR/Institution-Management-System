import os
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent)
APP_DIR = str(Path(__file__).parent)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

os.environ['TZ'] = 'Asia/Kolkata'
if hasattr(os, 'tzset'):
    import time
    time.tzset()

from dotenv import load_dotenv
env_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(env_path)
from database import MYSQL_SessionLocal, PG_SessionLocal, MYSQL_BASE, PG_BASE, MYSQL_Engine, PG_Engine
__all__ = ['MYSQL_SessionLocal', 'PG_SessionLocal', 'MYSQL_BASE', 'PG_BASE', 'MYSQL_Engine', 'PG_Engine', 'PROJECT_ROOT', 'APP_DIR']
