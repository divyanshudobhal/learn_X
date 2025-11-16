from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import json

# Backend helpers
from auth.auth_backend import login_user, signup_user, load_users
from chatbot_backend import ask_ai
from utils.ai_tags import generate_ai_tags
from utils.storage_utils import upload_file_with_metadata, delete_file, rename_file
from utils.pdf_utils import summarize_pdf
from utils.ai_logs import load_ai_logs, save_ai_log

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key")

# ======================================================
# PATH CONFIG (IMPORTANT FOR RENDER)
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


UPLOAD_RECORD = os.path.join(BASE_DIR, "uploads.json")
AI_LOGS_RECORD = os.path.join(BASE_DIR, "ai_logs.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================================================
# LOAD & SAVE Upload Metadata
# ======================================================
def load_uploads():
    if not os.path.exists(UPLOAD_RECORD):
        return []
    with open(UPLOAD_RECORD, "r") as f:
        return json.load(f)

def save_uploads(data):
    with open(UPLOAD_RECORD, "w") as f:
        json.dump(data, f, indent=4)


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
# ROUTES
# ======================================================

@app.route("/")
def home():
    return redirect(url_for("login"))


# --------------------- LOGIN ---------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

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
        u = request.form["username"]
        p = request.form["password"]
        r = request.form["role"]

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
        files=load_uploads()
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
    files = load_uploads()
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
    q = data.get("message", "")
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

        # Save metadata to uploads.json
        records = load_uploads()
        records.append({
            "uploaded_by": session["username"],
            "filename": filename,
            "url": s3_url,
            "tags": tags,
            "summary": summary
        })
        save_uploads(records)

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
    files = load_uploads()

    search = request.args.get("search", "").strip().lower()
    file_type = request.args.get("type", "all").lower()

    # ---- search ----
    if search:
        files = [
            f for f in files
            if search in f["filename"].lower()
            or any(search in t.lower() for t in f.get("tags", []))
        ]

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
    mine = [f for f in load_uploads() if f.get("uploaded_by") == session["username"]]
    return render_template("teacher_files.html", files=mine)


@app.post("/teacher/files/delete/<filename>")
@login_required("Teacher")
def delete_teacher_file(filename):
    records = load_uploads()
    records = [
        r for r in records
        if not (r["filename"] == filename and r.get("uploaded_by") == session["username"])
    ]

    # Delete from S3
    delete_file(filename)

    save_uploads(records)
    return redirect(url_for("teacher_files"))


@app.post("/teacher/files/rename/<filename>")
@login_required("Teacher")
def rename_teacher_file(filename):
    new_name = (request.form.get("new_name") or "").strip()
    if not new_name:
        return redirect(url_for("teacher_files"))

    records = load_uploads()
    for r in records:
        if r["filename"] == filename and r.get("uploaded_by") == session["username"]:
            # Rename in S3
            rename_file(filename, new_name)
            r["filename"] = new_name
            r["tags"] = generate_ai_tags(new_name)
            break

    save_uploads(records)
    return redirect(url_for("teacher_files"))


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
