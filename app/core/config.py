from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/school_db"
    SECRET_KEY: str = "change-this-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SCHOOL_NAME: str = "Greenfield Secondary School"
    SCHOOL_ADDRESS: str = "123 School Road, Lagos, Nigeria"
    SCHOOL_PHONE: str = "+234 800 000 0000"

    FIRST_ADMIN_EMAIL: str = "admin@school.com"
    FIRST_ADMIN_PASSWORD: str = "Admin@12345"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()