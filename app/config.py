from dotenv import load_dotenv
import os

load_dotenv()


DEBUG = bool(int(os.getenv("DEBUG", "0")))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 10

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")

SUPERUSER_EMAIL = os.getenv("SUPERUSER_EMAIL", "superuser@localhost.com")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "superuser")


ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")

HUGGINGFACE_EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cpu")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_TOKEN_LIMIT = int(os.getenv("MAX_TOKEN_LIMIT", 4096))
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

UPLOAD_FOLDER = "app/uploads"

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@redis:6379/0"
CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@redis:6379/0"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

LIQPAY_SANDBOX = bool(int(os.getenv("LIQPAY_SANDBOX", "0")))
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")



