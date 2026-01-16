# 🏃‍♂️ Sports Program — Jaya Academy

A Slack-based application designed to encourage physical activity, consistency, and healthy habits within the Jaya
community.  
This project is part of an internal learning initiative where developers collaborate, practice English, and gain
hands-on experience with modern backend development tools.

## 📌 Purpose

The main goal of this repository is to serve as a collaborative learning environment.  
Developers will learn by building a real system that integrates with Slack, uses a modern Python backend stack, follows
good engineering practices, and encourages teamwork.

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

The application uses the **Slack Bolt** framework to handle interactions. You need to configure your Slack App
credentials to allow the bot to communicate with the workspace.

### Configuration Steps

1. **Create or Select an App**:
    - Go to [Slack Apps](https://api.slack.com/apps).
    - Create a new app or select an existing one.

2. **Get Credentials**:
    - **Signing Secret**: Navigate to **Basic Information** > **App Credentials**. Copy the `Signing Secret`.
    - **Bot Token**: Navigate to **OAuth & Permissions** > **OAuth Tokens for Your Workspace**. Copy the
      `Bot User OAuth Token` (starts with `xoxb-`).

3. **Update Environment Variables**:
    - Open your `.env` file (copied from `.env.example`).
    - Fill in the variables:
      ```env
      SLACK_SIGNING_SECRET=your_signing_secret_here
      SLACK_BOT_TOKEN=xoxb-your-bot-token-here
      ```

4. **Development Setup**:
    - Ensure your bot has the required **Bot Token Scopes** (e.g., `commands`, `chat:write`, `app_mentions:read`) under
      **OAuth & Permissions**.
    - Reinstall the app to your workspace if you add new scopes.

## 🤝 Contributing

This project encourages:

- Frequent pull requests
- Pair programming
- English communication
- Documentation improvements
- Code reviews and refactoring

## 🧪 Tests and quality

Tests and Coverage:

```bash
poetry run pytest
```

*The coverage report is automatically generated in the terminal and in HTML format in the `htmlcov/` folder.*

Ruff (linter)

```bash
poetry run ruff check .  (add --fix to automatically fix rules)
poetry run ruff format .
```

## 🏁 License

MIT License.

Made with ❤️ by Jaya Academy.
