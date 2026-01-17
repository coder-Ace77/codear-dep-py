import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool


load_dotenv()

db_user = os.getenv('DB_USER') 
db_password = os.getenv('PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

encoded_password = urllib.parse.quote_plus(db_password)

# Note: Added sslmode=require for Aiven Cloud
SQLALCHEMY_DATABASE_URL = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?sslmode=require"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"sslmode": "require"},
    poolclass=NullPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Redis Configuration ---
# Note: Aiven Redis requires rediss:// (SSL) and decode_responses=True
redis_client = redis.from_url(
    f"rediss://default:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}",
    decode_responses=True
)