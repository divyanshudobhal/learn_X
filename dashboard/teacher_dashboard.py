import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
import datetime
import boto3
import threading
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# -------------------------------------------------
# Load ENV
# -------------------------------------------------
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET")
REGION = os.getenv("AWS_DEFAULT_REGION")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")  # e.g. dbci5xyzb8tw6.cloudfront.net

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOADS_JSON = os.path.join(BASE_DIR, "uploads.json")


# -------------------------------------------------
# AI TAG GENERATOR
# -------------------------------------------------
def generate_ai_tags(file_name):
    name = file_name.lower()
    tags = set()

    if "python" in name:
        tags.update(["Python", "Programming"])
    if "c " in name or name.startswith("c_") or " c" in name:
        tags.update(["C Language", "Coding"])
    if "dsa" in name or "data" in name:
        tags.update(["Data Structures", "Algorithms"])
    if "sql" in name or "db" in name:
        tags.update(["SQL", "Database"])
    if "ai" in name or "ml" in name:
        tags.update(["AI", "Machine Learning"])
    if "cloud" in name:
        tags.update(["Cloud", "AWS"])
    if "network" in name:
        tags.update(["Networking"])
    if "java" in name:
        tags.update(["Java", "OOP"])
    if "os" in name:
        tags.update(["Operating System"])
    if not tags:
        tags.update(["General Study Material"])

    return list(tags)


# -------------------------------------------------
# MIME TYPE HELPER
# -------------------------------------------------
def guess_mime_type(filename: str) -> str | None:
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return "application/pdf"
    if fn.endswith(".png"):
        return "image/png"
    if fn.endswith(".jpg") or fn.endswith(".jpeg"):
        return "image/jpeg"
    if fn.endswith(".txt"):
        return "text/plain"
    if fn.endswith(".mp4"):
        return "video/mp4"
    return None


# -------------------------------------------------
# TEACHER DASHBOARD
# -------------------------------------------------
class TeacherDashboard(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Window setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("Teacher Dashboard — E-Learning Cloud")
        self.geometry("1100x700")
        self.minsize(1000, 650)

        # Initialize S3 Client
        try:
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=REGION
            )
        except Exception as e:
            messagebox.showerror("AWS Error", f"Failed to connect to AWS:\n{e}")
            self.s3 = None

        # Ensure uploads.json exists
        if not os.path.exists(UPLOADS_JSON):
            with open(UPLOADS_JSON, "w") as f:
                json.dump([], f)

        # INTERNAL STATE
        self.selected_file_path = None
        self.selected_file_size = 0
        self._bytes_transferred = 0
        self._upload_cancelled = False

        # -------------------------------------------------
        # SIDEBAR
        # -------------------------------------------------
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar,
            text="E-Learn",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        ctk.CTkButton(
            self.sidebar,
            text="☁️ Upload",
            width=120,
            command=self.open_file_dialog
        ).pack(pady=10)

        ctk.CTkButton(
            self.sidebar,
            text="📁 View Uploads",
            width=120,
            command=self.view_uploads
        ).pack(pady=10)

        ctk.CTkButton(
            self.sidebar,
            text="💬 AI Assistant",
            width=120,
            command=self.open_chat
        ).pack(pady=10)

        ctk.CTkButton(
            self.sidebar,
            text="🚪 Logout",
            width=120,
            fg_color="#b00020",
            hover_color="#d32f2f",
            command=self.logout
        ).pack(side="bottom", pady=20)

        # -------------------------------------------------
        # MAIN CONTENT CENTERED
        # -------------------------------------------------
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            self.main_frame,
            text="Teacher Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            self.main_frame,
            text="Upload study materials to cloud with AI tagging",
            font=ctk.CTkFont(size=15)
        ).pack(pady=(0, 20))

        # Card frame
        self.card = ctk.CTkFrame(self.main_frame, width=850, height=420, corner_radius=12)
        self.card.pack()
        self.card.pack_propagate(False)

        # File info labels
        self.file_label = ctk.CTkLabel(self.card, text="No file selected", anchor="w")
        self.file_label.pack(fill="x", padx=20, pady=10)

        self.ai_tags_label = ctk.CTkLabel(self.card, text="AI Tags: —", anchor="w")
        self.ai_tags_label.pack(fill="x", padx=20)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self.card, width=700)
        self.progress.set(0)
        self.progress.pack(pady=20)

        # Buttons area
        btns = ctk.CTkFrame(self.card)
        btns.pack()

        self.choose_btn = ctk.CTkButton(
            btns, text="Choose File", width=140,
            command=self.open_file_dialog
        )
        self.choose_btn.grid(row=0, column=0, padx=10)

        self.start_upload_btn = ctk.CTkButton(
            btns, text="Start Upload", width=140,
            state="disabled", command=self.start_upload
        )
        self.start_upload_btn.grid(row=0, column=1, padx=10)

        self.cancel_upload_btn = ctk.CTkButton(
            btns, text="Cancel", width=140,
            state="disabled", command=self.cancel_upload
        )
        self.cancel_upload_btn.grid(row=0, column=2, padx=10)

        # Status
        self.status_label = ctk.CTkLabel(self.card, text="Status: Idle")
        self.status_label.pack(pady=10)

    # -------------------------------------------------
    # FILE SELECTION
    # -------------------------------------------------
    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Supported Files", "*.pdf *.mp4 *.png *.jpg *.jpeg *.txt"),
                ("All Files", "*.*")
            ]
        )
        if not path:
            return

        self.selected_file_path = path
        self.selected_file_size = os.path.getsize(path)

        filename = os.path.basename(path)
        self.file_label.configure(text=f"Selected: {filename}")
        tags = generate_ai_tags(filename)
        self.ai_tags_label.configure(text=f"AI Tags: {', '.join(tags)}")

        self.start_upload_btn.configure(state="normal")
        self.progress.set(0)
        self.status_label.configure(text="Status: Ready to upload")

    # -------------------------------------------------
    # UPLOAD PROCESS
    # -------------------------------------------------
    def start_upload(self):
        if not self.selected_file_path:
            messagebox.showerror("Error", "Please select a file first.")
            return

        if not self.s3:
            messagebox.showerror("AWS Error", "AWS S3 client was not initialized.")
            return

        self.start_upload_btn.configure(state="disabled")
        self.cancel_upload_btn.configure(state="normal")
        self.status_label.configure(text="Status: Uploading...")

        self._upload_cancelled = False
        self._bytes_transferred = 0

        threading.Thread(target=self._upload_to_s3_thread, daemon=True).start()

    def _upload_to_s3_thread(self):
        try:
            file_size = self.selected_file_size
            filename = os.path.basename(self.selected_file_path)

            mime = guess_mime_type(filename)
            extra_args = {}
            if mime:
                extra_args["ContentType"] = mime
                # Force inline preview (PDF/images/videos) instead of download
                extra_args["ContentDisposition"] = "inline"

            def progress_callback(chunk):
                if self._upload_cancelled:
                    raise Exception("Upload cancelled by user.")
                self._bytes_transferred += chunk
                progress = min(self._bytes_transferred / file_size, 1) if file_size > 0 else 0
                self.after(0, lambda: self.progress.set(progress))

            # Upload with progress + metadata
            with open(self.selected_file_path, "rb") as f:
                if extra_args:
                    self.s3.upload_fileobj(
                        f, BUCKET_NAME, filename,
                        ExtraArgs=extra_args,
                        Callback=progress_callback
                    )
                else:
                    self.s3.upload_fileobj(
                        f, BUCKET_NAME, filename,
                        Callback=progress_callback
                    )

            # Build URL for saving into uploads.json (for Admin / Teacher view)
            if CLOUDFRONT_DOMAIN:
                file_url = f"https://{CLOUDFRONT_DOMAIN}/{filename}"
            else:
                # Fallback: presigned URL (24 hours)
                file_url = self.s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": BUCKET_NAME, "Key": filename},
                    ExpiresIn=86400
                )

            tags = generate_ai_tags(filename)
            file_info = {
                "filename": filename,
                "url": file_url,  # used in Admin + teacher "View uploads"
                "uploaded_on": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tags": tags
            }

            uploads = self.load_uploads()
            uploads.append(file_info)
            self.save_uploads(uploads)

            self.after(0, lambda: self.progress.set(1))
            self.after(0, lambda: self.status_label.configure(text="Status: Upload complete ✓"))
            self.after(0, lambda: self.show_upload_success_popup(file_info))

        except Exception as e:
            if str(e) == "Upload cancelled by user.":
                self.after(0, lambda: self.status_label.configure(text="Status: Cancelled"))
            else:
                self.after(0, lambda: messagebox.showerror("Upload Error", str(e)))
                self.after(0, lambda: self.status_label.configure(text="Status: Failed"))
        finally:
            self.after(0, lambda: self.start_upload_btn.configure(state="disabled"))
            self.after(0, lambda: self.cancel_upload_btn.configure(state="disabled"))

    def cancel_upload(self):
        self._upload_cancelled = True
        self.status_label.configure(text="Status: Cancelling...")

    # -------------------------------------------------
    # SUCCESS POPUP
    # -------------------------------------------------
    def show_upload_success_popup(self, info):
        popup = ctk.CTkToplevel(self)
        popup.title("Upload Complete")
        popup.geometry("480x280")

        ctk.CTkLabel(
            popup,
            text="Upload Successful ✓",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        ctk.CTkLabel(popup, text=f"Filename: {info['filename']}").pack(pady=2)
        ctk.CTkLabel(popup, text=f"Tags: {', '.join(info['tags'])}", wraplength=420).pack(pady=4)

        def open_url():
            import webbrowser
            webbrowser.open(info["url"])

        ctk.CTkButton(popup, text="Open in Browser", command=open_url).pack(pady=10)
        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=5)

    # -------------------------------------------------
    # VIEW UPLOADS
    # -------------------------------------------------
    def view_uploads(self):
        uploads = self.load_uploads()
        if not uploads:
            messagebox.showinfo("Uploads", "No uploads recorded yet.")
            return

        win = ctk.CTkToplevel(self)
        win.title("Uploaded Files")
        win.geometry("780x520")

        header = ctk.CTkLabel(
            win,
            text="Uploaded Files (Cloud metadata)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=(10, 8))

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(expand=True, fill="both", padx=12, pady=8)

        for f in reversed(uploads):
            card = ctk.CTkFrame(scroll, corner_radius=8)
            card.pack(fill="x", padx=8, pady=8)

            ctk.CTkLabel(
                card,
                text=f"{f['filename']}",
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                card,
                text=f"Uploaded: {f['uploaded_on']} · Tags: {', '.join(f.get('tags', []))}",
                anchor="w",
                font=ctk.CTkFont(size=11)
            ).pack(fill="x", padx=12, pady=(0, 6))

            ctk.CTkLabel(
                card,
                text=f"URL: {f.get('url', '')}",
                anchor="w",
                font=ctk.CTkFont(size=10)
            ).pack(fill="x", padx=12, pady=(0, 4))

            button_row = ctk.CTkFrame(card)
            button_row.pack(padx=12, pady=(0, 10), anchor="e")

            ctk.CTkButton(
                button_row, text="Open", width=80,
                command=lambda url=f["url"]: self.open_url(url)
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                button_row, text="Copy URL", width=90,
                command=lambda url=f["url"]: self.copy_to_clipboard(url)
            ).pack(side="right", padx=4)

    def open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)

    def copy_to_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "URL copied to clipboard")

    # -------------------------------------------------
    # JSON HELPERS
    # -------------------------------------------------
    def load_uploads(self):
        try:
            with open(UPLOADS_JSON, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def save_uploads(self, data):
        with open(UPLOADS_JSON, "w") as f:
            json.dump(data, f, indent=4)

    # -------------------------------------------------
    # PLACEHOLDERS
    # -------------------------------------------------
    def open_chat(self):
        try:
            from dashboard.chatbot_ui import ChatbotUI
            ChatbotUI()
        except Exception as e:
            messagebox.showinfo("AI Assistant", f"Chatbot not available:\n{e}")

    def logout(self):
        self.destroy()
        from main import start_app
        start_app()


# Run directly for testing
if __name__ == "__main__":
    TeacherDashboard().mainloop()
