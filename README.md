School Result Management System

A production-ready REST API backend for managing student academic results in a Secondary School. Built with FastAPI, PostgreSQL, and SQLAlchemy (async).

Features
Role-based access control — Admin, Teacher, Student
JWT Authentication — Access + Refresh tokens
Academic structure — Academic years, 3 terms per year
Score entry — CA1 (20) + CA2 (20) + Exam (60) = 100
Auto grading — A, B, C, D, E, F with remarks
Class position — Each student's position in class per term
Affective domain — Punctuality, Neatness, Honesty, Sports, etc. (rated 1–5)
PDF report cards — Downloadable, fully formatted
Analytics — Per-subject and class-wide performance stats
Result publishing — Admin controls when students can see results
Async + Connection pooling — Handles 100–200 concurrent users comfortably
Auto ID generation — STU/2024/0001, TCH/2024/0001, ADM/2024/0001


Project Structure

student-result-system/
├── main.py                  
├── requirements.txt         
├── .env                     
└── app/
    ├── utils.py            
    ├── core/
    │   ├── config.py        
    │   ├── security.py      
    │   ├── grading.py       
    │   └── database.py      
    ├── models/
    │   └── models.py        
    ├── schemas/
    │   └── schemas.py       
    ├── services/
    │   ├── auth.py          
    │   ├── student.py       
    │   ├── teacher.py      
    │   ├── result.py       
    │   └── pdf.py           
    └── api/
        ├── router.py        
        ├── auth.py          
        ├── admin.py         
        ├── teacher.py      
        ├── student.py       
        └── result.py        



Installation & Setup (Windows)

Prerequisites
- Python 3.11+
- PostgreSQL 16 installed and running

Step 1 — Create the database
Open Command Prompt as Administrator:
cd "C:\Program Files\PostgreSQL\16\bin"
psql -U postgres

Inside psql:
CREATE DATABASE school_db;
\q


Step 2 — Set up the project
cd path\to\srs
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt


Step 3 — Configure environment
Open `.env` and update:
DATABASE_URL=postgresql+asyncpg://postgres:YOURPASSWORD@localhost:5432/school_db
SECRET_KEY=your-long-random-secret-key
SCHOOL_NAME=Your School Name
```

Step 4 — Run the server
uvicorn main:app --reload --port 8000


On first run, the super admin is automatically created:

Email:    admin@school.com
Password: Admin@12345

Change this password immediately after first login.



User Roles & Permissions

| Action                         | Admin | Teacher | Student |
|--------------------------------|-------|---------|---------|
| Create academic year / terms   | ✅    | ❌      | ❌      |
| Create subjects                | ✅    | ❌      | ❌      |
| Register teachers              | ✅    | ❌      | ❌      |
| Register students              | ✅    | ❌      | ❌      |
| Assign subjects to teachers    | ✅    | ❌      | ❌      |
| Enter / update results         | ✅    | ✅*     | ❌      |
| Enter affective domain scores  | ✅    | ✅      | ❌      |
| Publish / unpublish results    | ✅    | ❌      | ❌      |
| View all students' results     | ✅    | ✅      | ❌      |
| View own results only          | ❌    | ❌      | ✅**    |
| Download PDF report card       | ✅    | ✅      | ✅**    |
| View analytics                 | ✅    | ✅      | ❌      |

*Teachers can only enter results for subjects assigned to them.  
**Students can only access their own data, and only after admin publishes results.



Grading System

| Score Range | Grade | Remark     |
|-------------|-------|------------|
| 75 – 100    | A     | Excellent  |
| 65 – 74     | B     | Very Good  |
| 55 – 64     | C     | Good       |
| 45 – 54     | D     | Pass       |
| 40 – 44     | E     | Pass       |
| 0  – 39     | F     | Fail       |

Pass mark: 40%

Score breakdown:
- CA1 → max 20 marks
- CA2 → max 20 marks
- Exam → max 60 marks
- Total → 100 marks


Default Credentials

| Role    | Default Password         |
|---------|--------------------------|
| Admin   | `Admin@12345`            |
| Teacher | `teacher123`             |
| Student | Date of birth e.g. `2008-05-14` |

All users are forced to change their password on first login (`must_change_password: true`).


Class Levels
`JSS1` `JSS2` `JSS3` `SS1` `SS2` `SS3`



## 📋 First-Time Setup Order

After starting the server, do things in this exact order:

1. Login as admin
2. Create academic year (e.g. `2024/2025`)
3. Create terms (First, Second, Third)
4. Create subjects (Mathematics, English, etc.)
5. Register teachers
6. Assign subjects to teachers
7. Register students (assign class + academic year)
8. Teacher logs in → enters results
9. Admin publishes results
10. Student logs in → views result / downloads PDF


