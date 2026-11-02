# ☕ BrewScout

> **Smarter Workspace Discovery for Remote Workers, Coders, and Students.**

BrewScout is a full-stack web application designed to solve a specific modern problem: finding the perfect cafe for deep work, remote meetings, or study sessions. Unlike standard mapping apps that focus on food quality, BrewScout ranks locations based on a mathematically normalized **Workability Score**—evaluating critical factors like verified Wi-Fi speeds, power outlet density, noise levels, and backup power availability.

Repository: [https://github.com/AnthonyQuant/BrewScout](https://github.com/AnthonyQuant/BrewScout)  
Live Deployment: [https://brewscout-mv0b.onrender.com](https://brewscout-mv0b.onrender.com) *(Hosted on Render with Neon PostgreSQL)*

---

## 📋 Table of Contents
1. [The Problem & The Solution](#-the-problem--the-solution)
2. [Core Architecture & Features](#-core-architecture--features)
3. [Technology Stack](#-technology-stack)
4. [Environment Variables](#-environment-variables)
5. [Installation & Local Setup](#-installation--local-setup)
6. [Testing & Reliability](#-testing--reliability)
7. [Database Migrations](#-database-migrations)
8. [Workability Scoring Algorithm](#-workability-scoring-algorithm)

---

## 💡 The Problem & The Solution

**The Problem:** Traditional review platforms prioritize coffee taste, food menus, and aesthetic vibes. A remote worker doesn't just need good coffee; they need to know if the Wi-Fi can handle a Zoom call, if they'll have to fight for a wall socket, or if the cafe has backup generator power during grid outages.

**The Solution:** BrewScout introduces the **Workability Score**. It crowdsources and verifies operational metrics tailored specifically for digital nomads and students, allowing users to filter cafes by megabits-per-second, power outlet accessibility, and ambient noise levels.

---

## ✨ Core Architecture & Features

* **Smart Session Planner:** Input your activity (Coding, Studying, Team Meeting), duration, and priority. The algorithm dynamically renormalizes factor weights to recommend the absolute best matches for your specific work session, including minimum suitability thresholds.
* **Data Provenance & Quality:** Clear visible distinction between `Sample / Benchmark Data`, `Community Reported`, and `Admin Verified` metrics, ensuring high data credibility.
* **Strict Security Boundaries:** CSRF-protected `POST` endpoints for all state-changing actions (voting, moderation, deletion), open-redirect prevention, and strictly enforced environment secrets.
* **Scalable Discovery:** Database-side filtering (Min Wi-Fi, Price, Generator availability) and pagination to ensure fast load times as the directory grows.
* **Admin Moderation Queue:** All new submissions, community verification reports, and user reviews enter a secure queue for admin approval before altering public data.

---

## 🛠️ Technology Stack

* **Backend:** Python 3, Flask, SQLAlchemy (ORM), Gunicorn (WSGI)
* **Database:** SQLite (Development/Testing) / PostgreSQL (Production via Neon.tech)
* **Frontend:** HTML5, Jinja2 Templating, Bootstrap 5
* **Security:** Flask-WTF (CSRF), Werkzeug (Argon2 Hashing), HTTP-Only Cookies
* **Infrastructure:** Render (Hosting), Flask-Migrate/Alembic (Schema Migrations)

---

## 🔐 Environment Variables

Create a `.env` file in the root directory. The application will raise a `RuntimeError` at startup if critical production secrets are missing.

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Cryptographic key for session/CSRF tokens. | **Yes** | `your-secure-random-string` |
| `ADMIN_PASSWORD` | Password for the root admin dashboard. | **Yes** | `secure-admin-pass` |
| `ADMIN_EMAIL` | Email mapped to the admin account. | No | `admin@brewscout.com` |
| `DATABASE_URL` | PostgreSQL connection string for production. | No | `postgresql+psycopg2://user:pass@host/db` |

*(Note: If `DATABASE_URL` is omitted, the app defaults to a local SQLite database in the `instance/` folder for development).*

---

## 🚀 Installation & Local Setup

### 1. Clone & Activate Environment
```bash
git clone https://github.com/AnthonyQuant/BrewScout.git
cd BrewScout
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Run the non-destructive seeder script to populate benchmark cafes and initialize tables.
```bash
python seed.py
```

### 4. Run the Application
```bash
python app.py
```
Visit `http://127.0.0.1:5001` in your web browser.

---

## 🧪 Testing & Reliability

BrewScout includes an automated test suite verifying scoring bounds, authentication, authorization restrictions, and data invariants using an isolated in-memory SQLite database.

Run the test suite from the root directory:
```bash
python test_app.py
```
*Pass Criteria: All core routes, weight normalizations, and permission boundaries return expected HTTP status codes and valid state changes.*

---

## 🗄️ Database Migrations

Schema changes are handled via `Flask-Migrate`. If you add new models or columns, do not drop tables. Instead, run:

```bash
# Generate a new migration script based on model changes
flask db migrate -m "Added new column to Cafe"

# Apply changes to the database
flask db upgrade
```

---

## 🧮 Workability Scoring Algorithm

The base Workability Score is a strictly normalized weighted average:

* **Wi-Fi Quality:** 25%
* **Power Outlets:** 20%
* **Noise Level:** 20%
* **Seating Comfort:** 15%
* **Affordability:** 10%
* **Opening Hours:** 10%

When users launch the **Session Planner**, weights are dynamically adjusted based on session length and activity type. A strict normalization function ensures custom weights always sum to `1.0`, keeping final outputs bounded cleanly between `0.0` and `10.0`.