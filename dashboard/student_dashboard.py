import customtkinter as ctk
import os
import webbrowser
import boto3
from dotenv import load_dotenv
from tkinter import messagebox

# ----------------------------
# Load ENV
# ----------------------------
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET")
REGION = os.getenv("AWS_DEFAULT_REGION")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")  # e.g. dbci5xyzb8tw6.cloudfront.net

# S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)


# ----------------------------
# Tag helper (same logic as teacher)
# ----------------------------
def generate_ai_tags(filename: str):
    name = filename.lower()
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


class StudentDashboard(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Student Dashboard — E-Learning Cloud")
        self.geometry("950x650")
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        ctk.CTkLabel(
            self,
            text="🎓 Student Dashboard",
            font=("Arial Rounded MT Bold", 26)
        ).pack(pady=20)

        ctk.CTkLabel(
            self,
            text="Preview & download study materials uploaded by teachers",
            font=("Arial", 15)
        ).pack(pady=5)

        # ---------------- Search + Filter ----------------
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=350,
            placeholder_text="Search by filename or tags..."
        )
        self.search_entry.pack(side="left", padx=10)

        ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            command=self.search_files
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            search_frame,
            text="Show All",
            command=self.refresh_list
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            self,
            text="Filter by File Type:",
            font=("Arial", 13)
        ).pack(pady=5)

        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(
            self,
            values=["All", "PDF", "Video", "Image", "Other"],
            variable=self.filter_var,
            command=self.refresh_list
        )
        self.filter_menu.pack(pady=5)

        # ---------------- Scroll area ----------------
        self.list_frame = ctk.CTkScrollableFrame(self, width=850, height=360)
        self.list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # ---------------- Bottom buttons ----------------
        ctk.CTkButton(self, text="Refresh", command=self.refresh_list).pack(pady=5)
        ctk.CTkButton(self, text="💬 Chat Assistant", command=self.open_chatbot).pack(pady=5)
        ctk.CTkButton(self, text="Logout", fg_color="#b00020", hover_color="#d32f2f",
                      command=self.logout).pack(pady=10)

        self.refresh_list()

    # -------------------------------------------------
    # Fetch S3 Files
    # -------------------------------------------------
    def fetch_files(self):
        try:
            resp = s3.list_objects_v2(Bucket=BUCKET_NAME)
            if "Contents" not in resp:
                return []

            files = []
            for obj in resp["Contents"]:
                fname = obj["Key"]
                uploaded_on = obj["LastModified"].strftime("%Y-%m-%d %H:%M")

                # Build preview URL:
                # 1) Prefer CloudFront
                # 2) Fallback to presigned S3 URL
                if CLOUDFRONT_DOMAIN:
                    url = f"https://{CLOUDFRONT_DOMAIN}/{fname}"
                else:
                    mime = guess_mime_type(fname)
                    params = {"Bucket": BUCKET_NAME, "Key": fname}
                    if mime:
                        params["ResponseContentType"] = mime
                        params["ResponseContentDisposition"] = "inline"
                    url = s3.generate_presigned_url(
                        "get_object",
                        Params=params,
                        ExpiresIn=3600
                    )

                tags = generate_ai_tags(fname)

                files.append({
                    "filename": fname,
                    "uploaded_on": uploaded_on,
                    "url": url,
                    "tags": tags,
                })
            return files

        except Exception as e:
            messagebox.showerror("AWS Error", f"Failed to fetch files from S3:\n{e}")
            return []

    # -------------------------------------------------
    # UI List Handling
    # -------------------------------------------------
    def refresh_list(self, *args):
        for w in self.list_frame.winfo_children():
            w.destroy()

        all_files = self.fetch_files()
        if not all_files:
            ctk.CTkLabel(
                self.list_frame,
                text="No materials uploaded yet.",
                font=("Arial", 16)
            ).pack(pady=20)
            return

        file_type = self.filter_var.get()
        filtered = []

        for f in all_files:
            ext = os.path.splitext(f["filename"])[1].lower()

            if file_type == "PDF" and ext == ".pdf":
                filtered.append(f)
            elif file_type == "Video" and ext in [".mp4", ".avi", ".mov"]:
                filtered.append(f)
            elif file_type == "Image" and ext in [".png", ".jpg", ".jpeg"]:
                filtered.append(f)
            elif file_type == "Other" and ext not in [".pdf", ".mp4", ".avi", ".mov", ".png", ".jpg", ".jpeg"]:
                filtered.append(f)
            elif file_type == "All":
                filtered.append(f)

        if not filtered:
            ctk.CTkLabel(
                self.list_frame,
                text="No files found for this filter.",
                font=("Arial", 14)
            ).pack(pady=20)
            return

        for f in filtered:
            self.add_file_card(f)

    def add_file_card(self, file_info: dict):
        frame = ctk.CTkFrame(self.list_frame, corner_radius=10)
        frame.pack(fill="x", padx=15, pady=8)

        tags_text = ", ".join(file_info.get("tags", []))

        ctk.CTkLabel(
            frame,
            text=f"📄 {file_info['filename']}",
            font=("Arial Rounded MT Bold", 15)
        ).pack(anchor="w", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            frame,
            text=f"Uploaded: {file_info['uploaded_on']}",
            font=("Arial", 11)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            frame,
            text=f"AI Tags: {tags_text}",
            font=("Arial", 11),
            text_color="#00bcd4"
        ).pack(anchor="w", padx=10, pady=(0, 4))

        btns = ctk.CTkFrame(frame)
        btns.pack(anchor="e", padx=10, pady=6)

        ctk.CTkButton(
            btns,
            text="Preview",
            width=100,
            command=lambda fname=file_info["filename"]: self.preview_file(fname)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btns,
            text="Download",
            width=100,
            command=lambda fname=file_info["filename"]: self.download_file(fname)
        ).pack(side="left", padx=5)

    # -------------------------------------------------
    # Search
    # -------------------------------------------------
    def search_files(self):
        query = self.search_entry.get().lower().strip()
        if not query:
            self.refresh_list()
            return

        files = self.fetch_files()

        for w in self.list_frame.winfo_children():
            w.destroy()

        results = []
        for f in files:
            if query in f["filename"].lower() or query in " ".join(f["tags"]).lower():
                results.append(f)

        if not results:
            ctk.CTkLabel(
                self.list_frame,
                text="No results found.",
                font=("Arial", 14)
            ).pack(pady=20)
            return

        for f in results:
            self.add_file_card(f)

    # -------------------------------------------------
    # Preview & Download
    # -------------------------------------------------
    def preview_file(self, filename: str):
        try:
            # Use CloudFront if configured
            if CLOUDFRONT_DOMAIN:
                url = f"https://{CLOUDFRONT_DOMAIN}/{filename}"
            else:
                mime = guess_mime_type(filename)
                params = {"Bucket": BUCKET_NAME, "Key": filename}
                if mime:
                    params["ResponseContentType"] = mime
                    params["ResponseContentDisposition"] = "inline"

                url = s3.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=3600
                )

            webbrowser.open(url)

        except Exception as e:
            messagebox.showerror("Preview Error", f"Cannot open file in browser.\n{e}")

    def download_file(self, filename: str):
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            dest_path = os.path.join(downloads_dir, filename)

            s3.download_file(BUCKET_NAME, filename, dest_path)
            messagebox.showinfo("Downloaded", f"File saved to:\n{dest_path}")
        except Exception as e:
            messagebox.showerror("Download Error", f"Failed to download file.\n{e}")

    # -------------------------------------------------
    # Chatbot & Logout
    # -------------------------------------------------
    def open_chatbot(self):
        try:
            from dashboard.chatbot_ui import ChatbotUI
            ChatbotUI()
        except Exception as e:
            messagebox.showerror("Chatbot Error", f"Could not open chatbot.\n{e}")

    def logout(self):
        self.destroy()
        from main import start_app
        start_app()


# Run directly for testing
if __name__ == "__main__":
    StudentDashboard().mainloop()
