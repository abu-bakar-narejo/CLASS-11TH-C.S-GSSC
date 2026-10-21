import os
import sqlite3
from datetime import date, datetime
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "portal.db"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

SUBJECTS = ["Mathematics", "Physics", "English", "Computer Science"]

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()

def init_db():
    connection = sqlite3.connect(DATABASE)
    connection.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        created_at TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        due_date TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_id INTEGER NOT NULL,
        completed_at TEXT NOT NULL,
        UNIQUE(user_id, task_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )""")
    exists = connection.execute("SELECT id FROM users WHERE username=?", (ADMIN_USERNAME,)).fetchone()
    if not exists:
        connection.execute(
            "INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
            (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), "Portal Administrator", "admin", datetime.now().isoformat(timespec="seconds"))
        )
    count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        today = date.today().isoformat()
        samples = [
            ("Mathematics", "Revise today's textbook exercise", "Study the assigned STBB chapter and solve five questions in your notebook.", today),
            ("Physics", "Review definitions and formulas", "Write key definitions and practice formula-based questions from your current chapter.", today),
            ("English", "Grammar and vocabulary practice", "Revise one grammar topic and learn ten useful words.", today),
            ("Computer Science", "Practice the current chapter", "Review concepts and write short answers in your own words.", today),
        ]
        connection.executemany(
            "INSERT INTO tasks(subject,title,description,due_date,created_at) VALUES(?,?,?,?,?)",
            [(s,t,d,due,datetime.now().isoformat(timespec="seconds")) for s,t,d,due in samples]
        )
    connection.commit()
    connection.close()

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] != "admin":
            flash("Admin access is required for that page.", "error")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapped

BASE = r"""
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · Government Superior Science College</title>
<style>
:root{--navy:#10233f;--blue:#2457d6;--pale:#f2f6ff;--ink:#1e293b;--muted:#64748b;--line:#e2e8f0;--white:#fff;--green:#15803d;--red:#b91c1c}
*{box-sizing:border-box}body{margin:0;background:#f6f8fc;color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
a{color:var(--blue);text-decoration:none}.nav{background:var(--navy);color:#fff;padding:14px 5%;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
.brand{font-weight:800;letter-spacing:.1px}.brand small{display:block;font-weight:500;color:#cbd5e1;font-size:12px}.navlinks{display:flex;gap:15px;align-items:center;flex-wrap:wrap}.nav a{color:#fff}.nav .muted{color:#dbeafe}
.container{max-width:1120px;margin:28px auto;padding:0 18px}.hero{background:linear-gradient(125deg,#10233f,#2457d6);color:white;border-radius:22px;padding:30px;margin-bottom:22px}.hero h1{margin:0 0 8px;font-size:clamp(25px,4vw,38px);line-height:1.2}.hero p{margin:0;color:#e0eaff;max-width:720px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}.two{display:grid;grid-template-columns:1.3fr .7fr;gap:18px}.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:19px;box-shadow:0 5px 18px #0f172a08}.card h2,.card h3{margin:0 0 10px}.stat{font-size:30px;font-weight:800;color:var(--navy)}.muted{color:var(--muted)}.subject{border-top:4px solid var(--blue)}.pill{display:inline-block;border-radius:99px;background:#eaf0ff;color:#1d4ed8;padding:4px 10px;font-size:12px;font-weight:700}.task{display:flex;gap:12px;align-items:flex-start;border-bottom:1px solid var(--line);padding:14px 0}.task:last-child{border-bottom:0}.task input{margin-top:5px;width:18px;height:18px}.taskbody{flex:1;min-width:0}.task h3{font-size:16px;margin:0 0 4px}.done h3{text-decoration:line-through;color:var(--muted)}.btn,button{display:inline-block;border:0;border-radius:10px;padding:10px 15px;background:var(--blue);color:white;font-weight:700;cursor:pointer;font-size:14px}.btn.secondary,button.secondary{background:#eaf0ff;color:#1d4ed8}.btn.danger,button.danger{background:#fee2e2;color:#991b1b}.actions{display:flex;gap:8px;flex-wrap:wrap}.field{margin-bottom:14px}.field label{display:block;font-weight:700;margin-bottom:5px}.field input,.field select,.field textarea{width:100%;padding:11px 12px;border:1px solid #cbd5e1;border-radius:10px;background:white;font:inherit}.field textarea{min-height:90px;resize:vertical}.formcard{max-width:520px;margin:30px auto}.alert{padding:11px 14px;border-radius:10px;margin-bottom:12px;background:#dcfce7;color:#166534}.alert.error{background:#fee2e2;color:#991b1b}.progress{height:9px;background:#e2e8f0;border-radius:20px;overflow:hidden}.progress span{display:block;height:100%;background:#2563eb}.tablewrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:580px}th,td{text-align:left;padding:11px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-size:12px;text-transform:uppercase}.footer{text-align:center;color:var(--muted);padding:28px 12px;font-size:13px}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}.container{margin:18px auto}.hero{padding:23px}}
@media(max-width:480px){.grid{grid-template-columns:1fr}.nav{padding:13px 18px}.navlinks{gap:11px}.card{padding:15px}.hero{border-radius:15px}.actions .btn{flex:1;text-align:center}}
</style></head><body>
<header class="nav"><a class="brand" href="{{ url_for('dashboard') if user else url_for('login') }}">GS <small>Government Superior Science College · Class XI</small></a>
<div class="navlinks">{% if user %}<a href="{{ url_for('dashboard') }}">Dashboard</a>{% if user.role == 'admin' %}<a href="{{ url_for('admin') }}">Admin panel</a>{% endif %}<span class="muted">{{ user.full_name }}</span><a href="{{ url_for('logout') }}">Log out</a>{% else %}<a href="{{ url_for('login') }}">Login</a><a href="{{ url_for('register') }}">Student registration</a>{% endif %}</div></header>
<main class="container">{% with messages=get_flashed_messages(with_categories=true) %}{% for category,message in messages %}<div class="alert {{ 'error' if category=='error' else '' }}">{{ message }}</div>{% endfor %}{% endwith %}
{{ content|safe }}</main><footer class="footer">Class XI learning portal · Mathematics · Physics · English · Computer Science<br>Study support for the Sindh Textbook Board syllabus. Verify chapter assignments with your teachers.</footer></body></html>
"""

def page(title, content, **context):
    user = current_user()
    return render_template_string(BASE, title=title, content=render_template_string(content, user=user, **context), user=user)

@app.route("/")
def home():
    return redirect(url_for("dashboard") if current_user() else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(full_name) < 2 or len(password) < 8:
            flash("Enter a username (at least 3 characters), your name, and a password of at least 8 characters.", "error")
        else:
            try:
                db().execute("INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                    (username, generate_password_hash(password), full_name, "student", datetime.now().isoformat(timespec="seconds")))
                db().commit()
                flash("Account created. You can now log in.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username is already taken. Choose another.", "error")
    return page("Student registration", r"""
<div class="card formcard"><h1>Create student account</h1><p class="muted">Register to see daily tasks and track your progress.</p>
<form method="post"><div class="field"><label>Full name</label><input name="full_name" required maxlength="80" autocomplete="name"></div>
<div class="field"><label>Username</label><input name="username" required minlength="3" maxlength="40" autocomplete="username"></div>
<div class="field"><label>Password (at least 8 characters)</label><input type="password" name="password" required minlength="8" autocomplete="new-password"></div>
<button type="submit">Create account</button></form><p>Already registered? <a href="{{ url_for('login') }}">Log in</a></p></div>""")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        person = db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if person and check_password_hash(person["password_hash"], password):
            session.clear()
            session["user_id"] = person["id"]
            return redirect(url_for("admin" if person["role"] == "admin" else "dashboard"))
        flash("Incorrect username or password.", "error")
    return page("Login", r"""
<div class="card formcard"><h1>Welcome back</h1><p class="muted">Log in to your Class XI learning dashboard.</p>
<form method="post"><div class="field"><label>Username</label><input name="username" required autocomplete="username"></div>
<div class="field"><label>Password</label><input type="password" name="password" required autocomplete="current-password"></div><button type="submit">Log in</button></form>
<p>New student? <a href="{{ url_for('register') }}">Create an account</a></p><p class="muted">Admin login is configured by the website administrator.</p></div>""")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    tasks = db().execute("""SELECT t.*, CASE WHEN c.id IS NULL THEN 0 ELSE 1 END AS completed
        FROM tasks t LEFT JOIN completions c ON c.task_id=t.id AND c.user_id=?
        ORDER BY t.due_date ASC, t.id DESC""", (user["id"],)).fetchall()
    total = len(tasks)
    completed = sum(t["completed"] for t in tasks)
    progress = round(completed * 100 / total) if total else 0
    subject_stats = []
    for subject in SUBJECTS:
        subset = [t for t in tasks if t["subject"] == subject]
        done = sum(t["completed"] for t in subset)
        subject_stats.append({"name": subject, "total": len(subset), "done": done, "pct": round(done*100/len(subset)) if subset else 0})
    return page("Student dashboard", r"""
<section class="hero"><h1>Assalamu Alaikum, {{ user.full_name }} 👋</h1><p>Your Class XI study space. Complete today's tasks, build a consistent routine, and track your learning progress.</p></section>
<div class="grid" style="margin-bottom:18px"><div class="card"><div class="muted">Total tasks</div><div class="stat">{{ total }}</div></div><div class="card"><div class="muted">Completed</div><div class="stat">{{ completed }}</div></div><div class="card"><div class="muted">Remaining</div><div class="stat">{{ total-completed }}</div></div><div class="card"><div class="muted">Overall progress</div><div class="stat">{{ progress }}%</div><div class="progress"><span style="width:{{ progress }}%"></span></div></div></div>
<div class="grid" style="margin-bottom:18px">{% for s in subject_stats %}<div class="card subject"><span class="pill">{{ s.name }}</span><h3 style="margin-top:10px">{{ s.done }} / {{ s.total }} tasks</h3><div class="progress"><span style="width:{{ s.pct }}%"></span></div><p class="muted">{{ s.pct }}% completed</p></div>{% endfor %}</div>
<div class="two"><section class="card"><h2>Daily task list</h2><p class="muted">Tick a task when you finish it. Ask your teacher which chapter/exercise is currently assigned.</p>
{% if tasks %}{% for t in tasks %}<div class="task {{ 'done' if t.completed else '' }}"><form method="post" action="{{ url_for('toggle_task', task_id=t.id) }}"><input type="checkbox" aria-label="Mark task complete" onchange="this.form.submit()" {{ 'checked' if t.completed else '' }}></form><div class="taskbody"><h3>{{ t.title }}</h3><div><span class="pill">{{ t.subject }}</span> <span class="muted">Due {{ t.due_date }}</span></div><div class="muted">{{ t.description }}</div></div></div>{% endfor %}{% else %}<p>No tasks yet. Your admin can add tasks from the admin panel.</p>{% endif %}</section>
<aside class="card"><h2>Study checklist</h2><ul><li>Review class notes for 10 minutes.</li><li>Practice Mathematics problems.</li><li>Revise Physics definitions and formulas.</li><li>Read English and practice grammar.</li><li>Practice Computer Science concepts.</li><li>Prepare questions to ask your teacher.</li></ul><p class="muted">These are general suggestions, not official college assignments.</p></aside></div>
""", tasks=tasks, total=total, completed=completed, progress=progress, subject_stats=subject_stats)

@app.route("/task/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    user = current_user()
    task = db().execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("dashboard"))
    existing = db().execute("SELECT id FROM completions WHERE user_id=? AND task_id=?", (user["id"], task_id)).fetchone()
    if existing:
        db().execute("DELETE FROM completions WHERE id=?", (existing["id"],))
    else:
        db().execute("INSERT INTO completions(user_id,task_id,completed_at) VALUES(?,?,?)",
                     (user["id"], task_id, datetime.now().isoformat(timespec="seconds")))
    db().commit()
    return redirect(url_for("dashboard"))

@app.route("/admin")
@admin_required
def admin():
    tasks = db().execute("""SELECT t.*, (SELECT COUNT(*) FROM completions c WHERE c.task_id=t.id) AS completed_count
        FROM tasks t ORDER BY t.due_date ASC, t.id DESC""").fetchall()
    students = db().execute("""SELECT u.id,u.username,u.full_name,u.created_at,
        (SELECT COUNT(*) FROM completions c WHERE c.user_id=u.id) AS completed_count
        FROM users u WHERE u.role='student' ORDER BY u.full_name""").fetchall()
    return page("Admin panel", r"""
<section class="hero"><h1>Admin control panel</h1><p>Create daily tasks for Class XI subjects and check student completion counts.</p></section>
<div class="two"><section class="card"><h2>Add a daily task</h2><form method="post" action="{{ url_for('add_task') }}">
<div class="field"><label>Subject</label><select name="subject" required>{% for s in subjects %}<option>{{ s }}</option>{% endfor %}</select></div>
<div class="field"><label>Task title</label><input name="title" required maxlength="150" placeholder="e.g. Solve Exercise 2.1 questions"></div>
<div class="field"><label>Description / chapter / exercise</label><textarea name="description" maxlength="1000" placeholder="Add instructions for students"></textarea></div>
<div class="field"><label>Due date</label><input type="date" name="due_date" value="{{ today }}" required></div><button type="submit">Publish task</button></form></section>
<section class="card"><h2>Student overview</h2><div class="stat">{{ students|length }}</div><p class="muted">Registered student accounts</p><p>Students mark tasks complete from their own dashboard. Completion counts are shown below.</p></section></div>
<section class="card" style="margin-top:18px"><h2>Manage tasks</h2><div class="tablewrap"><table><thead><tr><th>Task</th><th>Subject</th><th>Due date</th><th>Completions</th><th>Action</th></tr></thead><tbody>{% for t in tasks %}<tr><td><strong>{{ t.title }}</strong><br><span class="muted">{{ t.description }}</span></td><td>{{ t.subject }}</td><td>{{ t.due_date }}</td><td>{{ t.completed_count }}</td><td><form method="post" action="{{ url_for('delete_task',task_id=t.id) }}" onsubmit="return confirm('Delete this task for all students?')"><button class="danger" type="submit">Delete</button></form></td></tr>{% else %}<tr><td colspan="5">No tasks published yet.</td></tr>{% endfor %}</tbody></table></div></section>
<section class="card" style="margin-top:18px"><h2>Registered students</h2><div class="tablewrap"><table><thead><tr><th>Name</th><th>Username</th><th>Joined</th><th>Tasks completed</th></tr></thead><tbody>{% for s in students %}<tr><td>{{ s.full_name }}</td><td>{{ s.username }}</td><td>{{ s.created_at[:10] }}</td><td>{{ s.completed_count }}</td></tr>{% else %}<tr><td colspan="4">No students have registered yet.</td></tr>{% endfor %}</tbody></table></div></section>
""", tasks=tasks, students=students, subjects=SUBJECTS, today=date.today().isoformat())

@app.route("/admin/tasks/add", methods=["POST"])
@admin_required
def add_task():
    subject = request.form.get("subject", "")
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "")
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        due_date = ""
    if subject not in SUBJECTS or not title or not due_date:
        flash("Please provide a valid subject, task title, and due date.", "error")
    else:
        db().execute("INSERT INTO tasks(subject,title,description,due_date,created_at) VALUES(?,?,?,?,?)",
            (subject,title,description,due_date,datetime.now().isoformat(timespec="seconds")))
        db().commit()
        flash("Task published to student dashboards.")
    return redirect(url_for("admin"))

@app.route("/admin/tasks/<int:task_id>/delete", methods=["POST"])
@admin_required
def delete_task(task_id):
    db().execute("DELETE FROM tasks WHERE id=?", (task_id,))
    db().commit()
    flash("Task deleted.")
    return redirect(url_for("admin"))

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
