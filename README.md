⭐ LearnX — Smart E-Learning Platform

LearnX is a modern, AI-powered e-learning platform built using Flask,
featuring:

🔐 User Authentication (Admin / Teacher / Student)

📤 Secure File Uploads

☁️ AWS S3 + CloudFront for global fast delivery

🤖 AI Chat Assistant

🔍 AI-generated tags for every uploaded file

📝 AI PDF Summaries

📂 Teacher File Manager

🎨 Beautiful Dark UI

🚀 Features
👨‍🏫 Teachers

Upload study materials (PDF, images, videos, docs)

Auto-generated AI tags

Auto summary for PDF files

Manage files (rename, delete, preview)

Clean and modern dashboard

🎓 Students

View all uploaded materials

Search by filename or tags

Filter by file type

Preview or download instantly

Use AI chatbot for help

🛡 Admins

View dashboards

Manage users (optional expansion)

🤖 AI Features

File Tag Generator

PDF Summarizer

Chatbot Assistant

🧱 Tech Stack
Layer	Technology
Backend	Flask (Python)
Storage	AWS S3
CDN	AWS CloudFront
AI	OpenAI API / Custom logic
UI	HTML, CSS, JS
Hosting	Render
📂 Project Structure
LEARNING_PLATFORM/
│
├── app.py
├── requirements.txt
├── Procfile
├── uploads.json
├── users.json
│
├── templates/
│   ├── dashboard_student.html
│   ├── dashboard_teacher.html
│   ├── teacher_files.html
│   ├── upload.html
│   ├── upload_success.html
│   ├── files.html
│   └── base.html
│
├── static/
│   ├── css/
│   │   └── custom.css
│   ├── images/
│   └── js/
│
├── utils/
│   ├── ai_tags.py
│   ├── pdf_utils.py
│   ├── s3_helper.py
│   ├── storage_utils.py
│   └── user_utils.py
│
├── auth_backend.py
└── chatbot_backend.py

⚙️ Environment Variables

The following variables must be added (Render → Environment):

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=eu-north-1
S3_BUCKET=e-learning-platform-files
CLOUDFRONT_DOMAIN=your-cloudfront-domain.cloudfront.net
FLASK_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key   (if chatbot uses OpenAI)

🚀 Run Locally
pip install -r requirements.txt
python app.py


App runs at:

http://127.0.0.1:5000

🌐 Deployment (Render)

Push this repo to GitHub

Create Web Service on Render

Add environment variables

Deploy

📦 Procfile
web: python app.py

📜 License

This project is for educational and personal use.

🙌 Contributors

Divyanshu Dobhal

⭐ WANT AN EVEN MORE PROFESSIONAL README?

I can add:

✔ Badges
✔ Screenshots
✔ Preview GIF
✔ API documentation
✔ Contribution section
