import customtkinter as ctk
import os
import json
from tkinter import messagebox
import boto3
from dotenv import load_dotenv

# -------------------------------------------------
# LOAD ENVIRONMENT
# -------------------------------------------------
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET")
REGION = os.getenv("AWS_DEFAULT_REGION")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
UPLOADS_FILE = os.path.join(BASE_DIR, "uploads.json")

# -------------------------------------------------
# AWS S3 CLIENT
# -------------------------------------------------
try:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION
    )
except Exception:
    s3 = None


# -------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------
class AdminDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Admin Dashboard — E-Learning Cloud")
        self.geometry("950x600")
        self.minsize(900, 550)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Title
        ctk.CTkLabel(
            self,
            text="🛡️ Admin Dashboard",
            font=("Arial Rounded MT Bold", 28)
        ).pack(pady=20)

        ctk.CTkLabel(
            self,
            text="Manage users, uploads, system health & cloud sync",
            font=("Arial", 16)
        ).pack(pady=10)

        # Buttons
        ctk.CTkButton(self, text="👥 View Users", width=250,
                      command=self.show_users).pack(pady=10)

        ctk.CTkButton(self, text="📂 View Uploaded Files", width=250,
                      command=self.show_uploads).pack(pady=10)

        ctk.CTkButton(self, text="📊 View System Statistics", width=250,
                      command=self.show_stats).pack(pady=10)

        ctk.CTkButton(self, text="🔄 Verify Cloud Sync", width=250,
                      command=self.verify_cloud_sync).pack(pady=10)

        ctk.CTkButton(self, text="🚪 Logout", width=250, fg_color="red",
                      command=self.logout).pack(pady=20)

    # -------------------------------------------------
    # LOAD JSON FILES
    # -------------------------------------------------
    def load_json(self, file_path):
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    # -------------------------------------------------
    # SHOW USERS
    # -------------------------------------------------
    def show_users(self):
        users = self.load_json(USERS_FILE)

        if not users:
            messagebox.showinfo("Users", "No registered users found!")
            return

        win = ctk.CTkToplevel(self)
        win.title("Registered Users")
        win.geometry("750x450")

        ctk.CTkLabel(
            win,
            text="👥 Registered Users",
            font=("Arial Rounded MT Bold", 22)
        ).pack(pady=15)

        scroll = ctk.CTkScrollableFrame(win, width=700, height=350)
        scroll.pack(pady=10)

        for username, info in users.items():
            role = info.get("role", "Unknown")
            ctk.CTkLabel(
                scroll,
                text=f"• {username}  ( {role} )",
                font=("Arial", 15)
            ).pack(anchor="w", padx=20, pady=6)

    # -------------------------------------------------
    # SHOW UPLOADED FILES
    # -------------------------------------------------
    def show_uploads(self):
        uploads = self.load_json(UPLOADS_FILE)

        if not uploads:
            messagebox.showinfo("Uploads", "No uploaded files found!")
            return

        win = ctk.CTkToplevel(self)
        win.title("Uploaded Files")
        win.geometry("850x500")

        ctk.CTkLabel(
            win,
            text="📂 Uploaded Files",
            font=("Arial Rounded MT Bold", 22)
        ).pack(pady=15)

        scroll = ctk.CTkScrollableFrame(win, width=800, height=400)
        scroll.pack(pady=10)

        for file in reversed(uploads):
            tags = ", ".join(file.get("tags", []))

            url = file.get("url", "")
            filename = file.get("filename", "")

            # Replace S3 link with CloudFront for display
            if CLOUDFRONT_DOMAIN:
                preview_url = f"https://{CLOUDFRONT_DOMAIN}/{filename}"
            else:
                preview_url = url

            ctk.CTkLabel(
                scroll,
                text=(
                    f"📄 {filename}\n"
                    f"🕒 {file['uploaded_on']}\n"
                    f"🏷️ Tags: {tags}\n"
                    f"🔗 {preview_url}"
                ),
                font=("Arial", 13),
                wraplength=750,
                justify="left"
            ).pack(anchor="w", padx=20, pady=10)

    # -------------------------------------------------
    # SYSTEM STATISTICS
    # -------------------------------------------------
    def show_stats(self):
        users = self.load_json(USERS_FILE)
        uploads = self.load_json(UPLOADS_FILE)

        total_users = len(users)
        roles = {"Student": 0, "Teacher": 0, "Admin": 0}

        for u in users.values():
            r = u.get("role", "")
            if r in roles:
                roles[r] += 1

        total_uploads = len(uploads)

        win = ctk.CTkToplevel(self)
        win.title("System Statistics")
        win.geometry("600x400")

        ctk.CTkLabel(
            win,
            text="📊 System Statistics",
            font=("Arial Rounded MT Bold", 22)
        ).pack(pady=15)

        ctk.CTkLabel(win, text=f"👥 Total Users: {total_users}", font=("Arial", 16)).pack(pady=6)
        ctk.CTkLabel(win, text=f"🎓 Students: {roles['Student']}", font=("Arial", 14)).pack(pady=3)
        ctk.CTkLabel(win, text=f"👨‍🏫 Teachers: {roles['Teacher']}", font=("Arial", 14)).pack(pady=3)
        ctk.CTkLabel(win, text=f"🛡️ Admins: {roles['Admin']}", font=("Arial", 14)).pack(pady=3)
        ctk.CTkLabel(win, text=f"📁 Total Files Uploaded: {total_uploads}", font=("Arial", 16)).pack(pady=12)

    # -------------------------------------------------
    # VERIFY CLOUD SYNC
    # -------------------------------------------------
    def verify_cloud_sync(self):
        if not s3:
            messagebox.showwarning("AWS", "AWS S3 is not configured!")
            return

        try:
            resp = s3.list_objects_v2(Bucket=BUCKET_NAME)
            cloud_files = [obj["Key"] for obj in resp.get("Contents", [])]
            local_files = [f["filename"] for f in self.load_json(UPLOADS_FILE)]

            missing = [f for f in local_files if f not in cloud_files]

            if missing:
                messagebox.showwarning(
                    "Sync Issue",
                    f"⚠️ Missing files in S3:\n{', '.join(missing)}"
                )
            else:
                messagebox.showinfo(
                    "Sync Success",
                    "✅ All uploaded files exist in AWS S3!"
                )

        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to check cloud sync.\n{e}")

    # -------------------------------------------------
    # LOGOUT
    # -------------------------------------------------
    def logout(self):
        self.destroy()
        from main import start_app
        start_app()


# Run directly
if __name__ == "__main__":
    AdminDashboard().mainloop()
