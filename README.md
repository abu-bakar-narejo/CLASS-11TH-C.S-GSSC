# Government Superior Science College — Class XI Portal

A responsive Flask + SQLite student portal with:
- Student registration/login
- Dashboard and task completion tracking
- Mathematics, Physics, English, and Computer Science task categories
- Admin task creation/deletion and student completion overview
- Mobile-friendly layout

## Deploy using a GitHub repository URL

1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `Procfile`.
2. On Render, create a **New Web Service** and connect that repository.
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Add environment variables in Render:
   - `SECRET_KEY` = a long, random secret value
   - `ADMIN_USERNAME` = your chosen admin username
   - `ADMIN_PASSWORD` = a strong password (at least 12 characters recommended)
5. Deploy. Render gives you a public `https://...` website URL.

## Important deployment notes

- GitHub stores the code; it does not itself run this Python website.
- SQLite is fine for a demo/small pilot. On many free hosting plans, local files may be temporary and can reset on redeploy/restart. For a real college-wide portal, use a persistent disk or a managed PostgreSQL database.
- Set `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` before making the website public. The default local admin login is `admin` / `ChangeMe123!`; do not use these defaults online.
- This is an independent study portal template, not an official college website. Use only school-approved branding and verify textbook chapter/exercise assignments with teachers.
- The starter tasks are examples; an admin should replace them with the actual current syllabus and daily assignments.
