# Primary School Management System (Django)

A role-based school management system with three dashboards:

- **Headteacher** — register students (admission numbers auto-generated as `ADM-<year>-<seq>`), manage classes, view all students.
- **Bursar** — view all students, record fee payments, automatic defaulter calculator (expected fee vs. paid per class/term/year).
- **Teacher** — view students in the class they lead, add subject results (auto-graded A–F).

All three dashboards can export their data as **PDF** (via ReportLab) and **Excel** (via openpyxl).

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo_data   # creates demo users + sample data
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and log in.

### Demo accounts (created by `seed_demo_data`)

| Role        | Username  | Password       |
|-------------|-----------|----------------|
| Headteacher | admin     | Admin@12345    |
| Bursar      | bursar    | Bursar@12345   |
| Teacher     | teacher1  | Teacher@12345  |

Change these passwords before any real use. `admin` is also a Django superuser — visit `/admin/` for full CRUD access to every model (subjects, fee structures, users, etc).

## How the pieces fit together

- `accounts` — custom `User` model with a `role` field (`HEADTEACHER` / `BURSAR` / `TEACHER`) and a `role_required` decorator used to guard every dashboard view.
- `students` — `SchoolClass` and `Student` models. `Student.save()` auto-generates the admission number the first time a record is created.
- `fees` — `FeeStructure` (expected amount per class/term/year) and `Payment` (amounts received). `fee_status_for_student()` / `all_defaulters()` compute expected vs. paid vs. balance and flag defaulters — this is the "automated fees calculator."
- `academics` — `Subject` and `Result` (with a simple A–F `grade()` method). Teachers can only add results for students in the one class where they are `class_teacher`.
- `reportsapp` — `export_pdf()` / `export_excel()` shared helpers used by every "Export PDF / Export Excel" button across all three dashboards.

## Extending it

- Add a `Term`/`AcademicYear` model if you want to lock which term is "current" school-wide, instead of typing it into a filter each time.
- Add report cards (per-student PDF combining all subjects for a term) — the `reportsapp.utils.export_pdf` helper can be reused for that with a different table layout.
- Add email/SMS notifications to guardians of defaulters using the `all_defaulters()` query.
- Swap SQLite for PostgreSQL in `settings.py` `DATABASES` before deploying.

## Production notes

This is configured for local development (`DEBUG = True`, SQLite, `ALLOWED_HOSTS = ["*"]`, a hard-coded `SECRET_KEY`). Before deploying: set `DEBUG = False`, generate a fresh `SECRET_KEY`, set real `ALLOWED_HOSTS`, switch to Postgres/MySQL, and serve static files properly (`collectstatic` + whitenoise or a CDN).
