from fastapi import APIRouter
from app.api import auth, admin, teacher, student, result

router = APIRouter(prefix="/api")

router.include_router(auth.router)
router.include_router(admin.router)
router.include_router(teacher.router)
router.include_router(student.router)
router.include_router(result.router)
