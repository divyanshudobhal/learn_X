import customtkinter as ctk
import google.generativeai as genai
from tkinter import messagebox
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Load API Key from .env (SAFE)
api_key = os.getenv("AIzaSyD952mhQGB06f6GEJKU5ayuB1y3ek_8SxI")
genai.configure(api_key=api_key)

class ChatbotUI(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("AI Learning Assistant 🤖")
        self.geometry("750x550")
        self.minsize(650, 500)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Header
        header = ctk.CTkLabel(
            self,
            text="💬 AI Learning Assistant",
            font=("Arial Rounded MT Bold", 22),
            text_color="#00bcd4"
        )
        header.pack(pady=15)

        # Chat Display Area
        self.chat_frame = ctk.CTkScrollableFrame(self, width=700, height=360, fg_color="#1a1a1a")
        self.chat_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Input Frame
        input_frame = ctk.CTkFrame(self, fg_color="#121212")
        input_frame.pack(fill="x", padx=10, pady=10)

        self.user_input = ctk.CTkEntry(input_frame, width=560, height=40,
                                       placeholder_text="Type your question...")
        self.user_input.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        self.user_input.bind("<Return>", lambda e: self.ask_ai())

        ctk.CTkButton(input_frame, text="Send", width=100, height=40,
                      command=self.ask_ai).pack(side="left", padx=5)

        # FIXED MODEL NAME ✔
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def ask_ai(self):
        question = self.user_input.get().strip()
        if not question:
            messagebox.showinfo("Info", "Please enter a question!")
            return

        self.add_message("🧑 You", question, "#0d47a1")
        self.user_input.delete(0, "end")

        # Thinking message
        self.add_message("🤖 AI", "Thinking...", "#333333")
        self.update_idletasks()

        try:
            response = self.model.generate_content(question)
            answer = response.text.strip()
        except Exception as e:
            answer = f"⚠️ Error: {e}"

        # Replace "Thinking..."
        for widget in reversed(self.chat_frame.winfo_children()):
            if isinstance(widget, ctk.CTkFrame):
                label = widget.winfo_children()[1]
                if "Thinking..." in label.cget("text"):
                    label.configure(text=answer)
                    break

    def add_message(self, sender, text, bg_color):
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=bg_color, corner_radius=10)
        msg_frame.pack(pady=6, padx=12, anchor="w" if sender == "🤖 AI" else "e", fill="x")

        ctk.CTkLabel(msg_frame, text=sender, font=("Arial Rounded MT Bold", 12),
                     text_color="#00e676").pack(anchor="w", padx=8, pady=(4, 0))

        ctk.CTkLabel(msg_frame, text=text, wraplength=600, justify="left",
                     font=("Arial", 13), text_color="white").pack(anchor="w", padx=8, pady=4)

        timestamp = datetime.datetime.now().strftime("%H:%M")
        ctk.CTkLabel(msg_frame, text=timestamp, font=("Arial", 10),
                     text_color="#888888").pack(anchor="e", padx=8, pady=(0, 4))

        self.chat_frame._parent_canvas.yview_moveto(1)
