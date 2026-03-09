import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

MYSQL_USER=os.getenv("MYSQL_USER")
MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD","")
MYSQL_HOST=os.getenv("MYSQL_HOST","localhost")
MYSQL_PORT=os.getenv("MYSQL_PORT","3306")
MYSQL_DATABASE=os.getenv("MYSQL_DATABASE")

POSTGRES_USER=os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD","")
POSTGRES_HOST=os.getenv("POSTGRES_HOST","localhost")
POSTGRES_PORT=os.getenv("POSTGRES_PORT","5432")
POSTGRES_DATABASE=os.getenv("POSTGRES_DATABASE")

MYSQL_URL=(
    f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)
POSTGRES_URL=(
    f"postgresql+psycopg2://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
)

MYSQL_BASE=declarative_base()
PG_BASE=declarative_base()

MYSQL_Engine=create_engine(MYSQL_URL,pool_pre_ping=True)
MYSQL_SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=MYSQL_Engine)

PG_Engine=create_engine(POSTGRES_URL,pool_pre_ping=True)
PG_SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=PG_Engine)

def get_db():
    db=MYSQL_SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_pg_db():
    db=PG_SessionLocal()
    try:
        yield db
    finally:
        db.close()
