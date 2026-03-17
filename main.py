from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models.models import Base
from app.api.router import router


async def create_first_admin():
    """Create the super admin account on first run if none exists."""
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models.models import User, Admin, Role
    from app.utils import gen_admin_id
    from sqlalchemy import select

    async with SessionLocal() as db:
        try:
            exists = (await db.execute(select(User).where(User.role == Role.ADMIN))).scalar_one_or_none()
            if exists:
                return

            print("🔧 Creating first super admin...")
            user = User(
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role=Role.ADMIN,
                must_change_password=False,
            )
            db.add(user)
            await db.flush()

            admin = Admin(
                user_id=user.id,
                admin_id=gen_admin_id(2024, 1),
                first_name="Super",
                last_name="Admin",
            )
            db.add(admin)
            await db.commit()
            print(f"✅ Admin created → Email: {settings.FIRST_ADMIN_EMAIL}  Password: {settings.FIRST_ADMIN_PASSWORD}")
            print("   ⚠️  Change this password after first login!")
        except Exception as e:
            await db.rollback()
            print(f"❌ Could not create admin: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + seed admin
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await create_first_admin()
    yield
    # Shutdown: close DB pool
    await engine.dispose()


app = FastAPI(
    title="School Result Management System",
    version="1.0.0",
    description="Backend for a Secondary School Result Management System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Lock this down to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
