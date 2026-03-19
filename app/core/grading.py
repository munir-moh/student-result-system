PASS_MARK = 40
CA1_MAX   = 20
CA2_MAX   = 20
EXAM_MAX  = 60

GRADE_SCALE = [
    (75, 100, "A", "Excellent"),
    (65,  74, "B", "Very Good"),
    (55,  64, "C", "Good"),
    (45,  54, "D", "Pass"),
    (40,  44, "E", "Pass"),
    (0,   39, "F", "Fail"),
]

AFFECTIVE_LABELS = {5: "Excellent", 4: "Very Good", 3: "Good", 2: "Fair", 1: "Poor"}


def get_grade(score: float) -> tuple:
    for low, high, letter, remark in GRADE_SCALE:
        if low <= round(score) <= high:
            return letter, remark, score >= PASS_MARK
    return "F", "Fail", False


def get_comment(average: float) -> str:
    if average >= 75: return "Outstanding performance. Keep it up!"
    if average >= 65: return "Very good performance. Strive for excellence."
    if average >= 55: return "Good performance. Room for improvement."
    if average >= 45: return "Fair performance. More effort is needed."
    if average >= 40: return "Pass. Significant improvement is required."
    return "Poor performance. Urgent attention needed."


def validate_scores(ca1: float, ca2: float, exam: float) -> list:
    errors = []
    if not (0 <= ca1 <= CA1_MAX):   errors.append(f"CA1 must be 0–{CA1_MAX}")
    if not (0 <= ca2 <= CA2_MAX):   errors.append(f"CA2 must be 0–{CA2_MAX}")
    if not (0 <= exam <= EXAM_MAX): errors.append(f"Exam must be 0–{EXAM_MAX}")
    return errors
