from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

# Database
from db import init_db, get_db_connection

# Backend helpers
from auth.auth_backend import login_user, signup_user, load_users
from chatbot_backend import ask_ai
from utils.ai_tags import generate_ai_tags
from utils.storage_utils import upload_file_with_metadata, delete_file, rename_file
from utils.pdf_utils import summarize_pdf
from utils.ai_logs import load_ai_logs, save_ai_log

from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key")

# ======================================================
# PATH CONFIG (for temporary upload storage only)
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ======================================================
# Login Required Decorator
# ======================================================
def login_required(role=None):
    def wrapper(fn):
        def decorated(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper


# ======================================================
# UPLOAD HELPERS (DB)
# ======================================================
def db_get_uploads():
    """Return list of uploads as dicts (with tags as list)."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, uploaded_by, filename, url, tags, summary, uploaded_at
        FROM uploads
        ORDER BY uploaded_at DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert tags "a,b,c" -> ["a","b","c"]
    for r in rows:
        tags_str = r.get("tags") or ""
        if tags_str.strip():
            r["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
        else:
            r["tags"] = []
    return rows


def db_add_upload(upload_dict: dict):
    """Insert a new upload row into DB."""
    conn = get_db_connection()
    cur = conn.cursor()
    tags_list = upload_dict.get("tags") or []
    tags_str = ",".join(tags_list)

    cur.execute("""
        INSERT INTO uploads (uploaded_by, filename, url, tags, summary)
        VALUES (%s, %s, %s, %s, %s);
    """, (
        upload_dict["uploaded_by"],
        upload_dict["filename"],
        upload_dict["url"],
        tags_str,
        upload_dict.get("summary")
    ))

    conn.commit()
    cur.close()
    conn.close()


def db_delete_upload(filename: str, username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM uploads
        WHERE filename = %s AND uploaded_by = %s;
    """, (filename, username))
    conn.commit()
    cur.close()
    conn.close()


def db_rename_upload(old_name: str, new_name: str, username: str, new_tags):
    conn = get_db_connection()
    cur = conn.cursor()
    tags_str = ",".join(new_tags) if new_tags else ""
    cur.execute("""
        UPDATE uploads
        SET filename = %s, tags = %s
        WHERE filename = %s AND uploaded_by = %s;
    """, (new_name, tags_str, old_name, username))
    conn.commit()
    cur.close()
    conn.close()


# ======================================================
# APP STARTUP: INIT DB
# ======================================================
@app.before_first_request
def before_first_request():
    init_db()


# ======================================================
# ROUTES
# ======================================================

@app.route("/")
def home():
    return redirect(url_for("login"))


# --------------------- LOGIN ---------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        success, msg, user = login_user(username, password)
        if not success:
            return render_template("login.html", error=msg)

        session["username"] = username
        session["role"] = user["role"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# --------------------- SIGNUP ---------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        r = request.form.get("role", "")

        ok, msg = signup_user(u, p, r)
        if not ok:
            return render_template("signup.html", error=msg)

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------- DASHBOARD Logic ---------------------
@app.route("/dashboard")
@login_required()
def dashboard():
    role = session["role"]
    if role == "Admin":
        return redirect(url_for("admin_dashboard"))
    if role == "Teacher":
        return redirect(url_for("teacher_dashboard"))
    return redirect(url_for("student_dashboard"))


# --------------------- STUDENT ---------------------
@app.route("/dashboard/student")
@login_required("Student")
def student_dashboard():
    return render_template(
        "student_dashboard.html",
        username=session["username"],
        files=db_get_uploads()
    )


# --------------------- TEACHER ---------------------
@app.route("/dashboard/teacher")
@login_required("Teacher")
def teacher_dashboard():
    return render_template(
        "teacher_dashboard.html",
        username=session["username"]
    )


# --------------------- ADMIN ---------------------
@app.route("/dashboard/admin")
@login_required("Admin")
def admin_dashboard():
    users = load_users()
    files = db_get_uploads()
    ai_logs = load_ai_logs()

    return render_template(
        "admin_dashboard.html",
        username=session["username"],
        total_users=len(users),
        total_files=len(files),
        ai_queries=len(ai_logs),
        users=users,
        files=files,
        ai_logs=ai_logs
    )


# ======================================================
# CHATBOT
# ======================================================
@app.route("/chatbot")
@login_required()
def chatbot():
    return render_template("chatbot.html")


@app.post("/api/chat")
@login_required()
def api_chat():
    data = request.get_json() or {}
    q = data.get("message", "").strip()
    ans = ask_ai(q)
    save_ai_log(q, ans, session["username"])
    return {"answer": ans}


# ======================================================
# UPLOAD (TEACHER)
# ======================================================
@app.route("/upload", methods=["GET", "POST"])
@login_required("Teacher")
def upload_page():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return render_template("upload.html", error="Select a file!")

        filename = secure_filename(file.filename)
        if not filename:
            return render_template("upload.html", error="Invalid filename.")

        # Save temporarily to /uploads folder (local)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)

        # Upload to S3 -> CloudFront
        s3_url = upload_file_with_metadata(temp_path, key=filename)

        # AI tags + optional PDF summary
        tags = generate_ai_tags(filename)
        summary = summarize_pdf(temp_path) if filename.lower().endswith(".pdf") else None

        # Save metadata to DB
        db_add_upload({
            "uploaded_by": session["username"],
            "filename": filename,
            "url": s3_url,
            "tags": tags,
            "summary": summary
        })

        # Remove local temp
        os.remove(temp_path)

        return render_template("upload_success.html", url=s3_url, tags=tags)

    return render_template("upload.html")


# ======================================================
# FILE SEARCH + FILTER (Student view)
# ======================================================
@app.route("/files")
@login_required()
def files_page():
    files = db_get_uploads()

    search = (request.args.get("search") or "").strip().lower()
    file_type = (request.args.get("type") or "all").lower()

    # ---- search ----
    if search:
        filtered = []
        for f in files:
            filename_match = search in f["filename"].lower()
            tags_match = any(search in t.lower() for t in f.get("tags", []))
            if filename_match or tags_match:
                filtered.append(f)
        files = filtered

    # ---- type filter ----
    if file_type != "all":
        def match(file):
            name = file["filename"].lower()

            if file_type == "pdf":
                return name.endswith(".pdf")
            if file_type == "image":
                return any(name.endswith(e) for e in [".jpg", ".jpeg", ".png", ".gif"])
            if file_type == "video":
                return any(name.endswith(e) for e in [".mp4", ".mov", ".avi", ".mkv"])
            if file_type == "doc":
                return any(name.endswith(e) for e in [".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"])
            # "other" or unknown -> allow all
            return True

        files = [f for f in files if match(f)]

    return render_template(
        "student_dashboard.html",
        files=files,
        username=session["username"]
    )


# ======================================================
# TEACHER FILE MANAGER
# ======================================================
@app.route("/teacher/files")
@login_required("Teacher")
def teacher_files():
    all_files = db_get_uploads()
    mine = [f for f in all_files if f.get("uploaded_by") == session["username"]]
    return render_template("teacher_files.html", files=mine)


@app.post("/teacher/files/delete/<filename>")
@login_required("Teacher")
def delete_teacher_file(filename):
    # Delete from S3
    delete_file(filename)

    # Delete from DB
    db_delete_upload(filename, session["username"])

    return redirect(url_for("teacher_files"))


@app.post("/teacher/files/rename/<filename>")
@login_required("Teacher")
def rename_teacher_file(filename):
    new_name = (request.form.get("new_name") or "").strip()
    if not new_name:
        return redirect(url_for("teacher_files"))

    # Generate fresh tags
    new_tags = generate_ai_tags(new_name)

    # Rename in S3
    rename_file(filename, new_name)

    # Update DB
    db_rename_upload(filename, new_name, session["username"], new_tags)

    return redirect(url_for("teacher_files"))


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
