# 🏃‍♂️ Sports Program — Jaya Academy

A Slack-based application designed to encourage physical activity, consistency, and healthy habits within the Jaya community.  
This project is part of an internal learning initiative where developers collaborate, practice English, and gain hands-on experience with modern backend development tools.

## 📌 Purpose
The main goal of this repository is to serve as a collaborative learning environment.  
Developers will learn by building a real system that integrates with Slack, uses a modern Python backend stack, follows good engineering practices, and encourages teamwork.

## 🧰 Tech Stack

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python)
![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Manager-60A5FA?logo=poetry)
![FastAPI](https://img.shields.io/badge/FastAPI-0.123-009688?logo=fastapi)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-red?logo=sqlalchemy)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange)
![Slack Bolt](https://img.shields.io/badge/Slack%20Bolt-Bot-green?logo=slack)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-316192?logo=postgresql)
![SQLite](https://img.shields.io/badge/SQLite-Local%20Dev-003B57?logo=sqlite)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)

## 🚀 Getting Started

### 1. Clone the repository
```
git clone https://github.com/jaya-academy/sports-program.git
cd sports-program
```

### 2. Install dependencies
```bash
poetry install
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run migrations
```bash
poetry run alembic upgrade head
```

### 5. Start the API
```bash
poetry run uvicorn app.main:app --reload
```

### Alternative: Enter Poetry shell
```bash
poetry shell
uvicorn app.main:app --reload
```

## 🤖 Slack Integration
1. Create a Slack App  
2. Enable required permissions  
3. Set up event subscriptions  
4. Use ngrok or Cloudflare Tunnel to expose your API  
5. Connect Slack events to FastAPI routes

## 🤝 Contributing
This project encourages:
- Frequent pull requests  
- Pair programming  
- English communication  
- Documentation improvements  
- Code reviews and refactoring

## 🧪 Tests
```bash
poetry run pytest
```

## 🏁 License
MIT License.

Made with ❤️ by Jaya Academy.
