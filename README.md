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

The application uses the **Slack Bolt** framework with **OAuth** support. This allows the app to be installed in multiple workspaces.

### Configuration Steps

1. **Create or Select an App**:
    - Go to [Slack Apps](https://api.slack.com/apps).

2. **Get OAuth Credentials**:
    - **Client ID & Client Secret**: Navigate to **Basic Information** > **App Credentials**.
    - **Signing Secret**: Also in **Basic Information**.

3. **Update Environment Variables**:
    - Open your `.env` file and fill in:
      ```env
      SLACK_CLIENT_ID=your_client_id
      SLACK_CLIENT_SECRET=your_client_secret
      SLACK_SIGNING_SECRET=your_signing_secret
      SLACK_SCOPES=commands,chat:write
      ```

4. **OAuth & Permissions**:
    - Add the Redirect URL: `https://your-domain.com/slack/oauth_redirect`.
    - Ensure required scopes are added.

5. **Installation Entry Point**:
    - The application provides a default installation page at `/slack/install`.
    - This page contains the **Add to Slack** button which initiates the OAuth flow for new workspaces.

## 🧪 Local Testing Guide

To test the Slack integration locally, you need to expose your local server to the internet using a tool like **ngrok**.

### 1. Preparar o Ambiente Local
1. Instale e execute o ngrok:
   ```bash
   ngrok http 8000
   ```
2. Copie a URL gerada (ex: `https://abcd-123.ngrok-free.app`).

### 2. Configurar o Slack App Dashboard
No [Slack App Dashboard](https://api.slack.com/apps):

1. **OAuth & Permissions**: Adicione a Redirect URL usando o seu ngrok: `https://abcd-123.ngrok-free.app/slack/oauth_redirect`.
2. **Event Subscriptions**: Ative e configure a Request URL: `https://abcd-123.ngrok-free.app/slack/events`.
3. **Slash Commands**: Garanta que os comandos apontem para a URL de eventos acima.

### 3. Instalação e Validação
1. Inicie o servidor: `poetry run uvicorn app.main:app --reload`
2. Acesse: `https://abcd-123.ngrok-free.app/slack/install`
3. Clique em **Add to Slack** e autorize.
4. Teste um comando no Slack (ex: `/list-programs`).

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
