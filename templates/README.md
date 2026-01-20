# 🌍 Global Board Architecture Kit (Python FastAPI)

> **A Python-based educational kit comparing Eastern vs. Western web board architectures.**
> 한국형 리스트 게시판부터 글로벌 피드형 UI까지, 웹 문화의 차이를 기술로 구현하는 교육용 프로젝트입니다.

## 📖 Project Overview (프로젝트 개요)
This project is designed for **Junior Developers** and **CS Students** to learn the full-cycle of web development using Python. It goes beyond simple CRUD, exploring how cultural differences impact software architecture.

이 프로젝트는 단순한 코딩 교육을 넘어, 문화적 차이가 소프트웨어 아키텍처에 미치는 영향을 탐구합니다.

## 🛠 Tech Stack (기술 스택)
- **Backend:** Python 3.10+, FastAPI
- **Database:** SQLite (SQLAlchemy ORM)
- **Security:** JWT Authentication, HttpOnly Cookie, Bcrypt Hashing
- **Frontend:** Jinja2 Templates, Bootstrap 5 (Responsive)

## 🚀 Key Features (핵심 기능)

### 1. Robust Authentication (보안 인증)
- Implementing **JWT (JSON Web Tokens)** standard.
- Preventing XSS attacks using **HttpOnly Cookies**.
- **Password Hashing** for database security.

### 2. Full-Stack CRUD (데이터 처리)
- Create, Read, Update, Delete posts with **Owner Permission Checks**.
- **AJAX (Fetch API)** integration for seamless UX (No page reload).

### 3. Educational Modules (교육 모듈)
- **Module A (List View):** Optimized for searching & archiving (Korean Style).
- **Module B (Feed View):** Optimized for content consumption (Global Style - *Planned*).
- **Module C (Data Analysis):** Visualizing user activity with Charts (*Planned*).

## 📂 Project Structure
```bash
├── main.py            # Entry point & API Routes
├── models.py          # DB Schema Definitions
├── auth.py            # Security & Token Logic
├── templates/         # HTML/UI Files
│   ├── base.html      # Layout Skeleton
│   ├── index.html     # Dashboard UI
│   └── login.html     # Auth UI
└── README.md          # You are here!