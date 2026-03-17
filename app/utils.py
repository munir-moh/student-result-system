def gen_admin_id(year: int, count: int) -> str:
    return f"ADM/{year}/{count:04d}"


def gen_staff_id(year: int, count: int) -> str:
    return f"TCH/{year}/{count:04d}"


def gen_student_id(year: int, count: int) -> str:
    return f"STU/{year}/{count:04d}"
