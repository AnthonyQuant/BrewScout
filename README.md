# ☕ BrewScout

> **Smarter Workspace Discovery for Remote Workers, Coders, and Students.**

BrewScout is a full-stack web application designed to solve a specific modern problem: finding the perfect cafe for deep work, remote meetings, or study sessions. Unlike standard mapping apps that focus on food quality, BrewScout ranks locations based on their **Workability Score**—evaluating critical factors like verified Wi-Fi speeds, power outlet density, noise levels, and backup power availability.

---

## 📋 Table of Contents
1. [The Problem & The Solution](#-the-problem--the-solution)
2. [Core Features](#-core-features)
3. [Technology Stack](#-technology-stack)
4. [Installation & Local Setup](#-installation--local-setup)
5. [Usage Guide](#-usage-guide)
6. [Workability Scoring System](#-workability-scoring-system)
7. [Database Architecture](#-database-architecture)
8. [Future Roadmap](#-future-roadmap)

---

## 💡 The Problem & The Solution

**The Problem:** Traditional review platforms (like Google Maps or Yelp) prioritize coffee taste, food menus, and aesthetic vibes. A remote worker doesn't just need good coffee; they need to know if the Wi-Fi can handle a Zoom call, if they'll have to fight for a wall socket, or if the cafe has backup power during grid outages.

**The Solution:** BrewScout introduces the **Workability Score**. It crowdsources and verifies operational metrics tailored specifically for digital nomads and students, allowing users to filter cafes by megabits-per-second, power outlet accessibility, and ambient noise levels.

---

## ✨ Core Features

### 🔍 Advanced Workspace Search & Filtering
* **Granular Filters:** Filter locations by Minimum Wi-Fi Speed (e.g., 50+ Mbps), Price Preference, and Generator/Backup Power availability.
* **Smart Sorting:** Sort results by Best Workability Score, Fastest Wi-Fi, Most Outlets, or Most Affordable.
* **Live Map Previews:** Instantly preview a neighborhood or specific cafe via a dynamic zero-cost Google Maps iframe embed based on search queries.

### 📊 The Workability Scoring Algorithm
* Calculates a weighted score (out of 10) based on Wi-Fi quality, power outlet density, seating comfort, noise levels, affordability, and opening hours.

### 🗓️ Smart Session Planner
* Tell BrewScout what you plan to do (Coding, Studying, Team Meeting, Casual Reading), how long you plan to stay, and your priority (Wi-Fi, Quiet, Budget). 
* The algorithm recalculates weights dynamically to recommend the absolute best matches for your specific work session.

### ⚖️ Side-by-Side Comparison Matrix
* Add up to 4 cafes to a comparison matrix.
* View a side-by-side breakdown of all metrics (Wi-Fi speed, socket density, meeting friendliness) to make an informed choice.

### 👥 Community-Driven Data & Moderation
* **Add Cafes:** Authenticated users can submit new workspaces.
* **Verification Reports:** Users can submit updates (e.g., "The Wi-Fi is faster now" or "Prices increased") to keep data fresh.
* **Reviews & Upvotes:** Leave detailed session reviews, reply to others, and upvote/downvote helpful comments.
* **Admin Moderation Queue:** All new submissions, reviews, and reports enter a pending queue to ensure high data quality and prevent spam.

### 📈 Global Analytics Dashboard
* A macro-view of the workspace landscape. View the percentage of cafes with backup power, average area Wi-Fi speeds, and top-ranked spots at a glance.

---

## 🛠️ Technology Stack

* **Backend:** Python 3, Flask, SQLAlchemy (ORM)
* **Database:** SQLite (Development) / PostgreSQL (Production ready via environment variables)
* **Frontend:** HTML5, Jinja2 Templating, Bootstrap 5, Custom CSS, Vanilla JavaScript
* **Forms & Security:** Flask-WTF, Werkzeug (Password Hashing), Secure HTTP-Only Cookies
* **Mapping:** Dynamic Google Maps Embed URLs

---

## 🚀 Installation & Local Setup

Follow these steps to get BrewScout running on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/brewscout.git
cd brewscout
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install Flask Flask-SQLAlchemy Flask-WTF python-dotenv Werkzeug
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and add the following:
```env
SECRET_KEY=your-super-secret-development-key
ADMIN_EMAIL=admin@brewscout.com
ADMIN_PASSWORD=admin123
```

### 5. Initialize & Seed the Database
Run the seeder script to build the database schema and populate it with initial sample data and the admin account.
```bash
python seed.py
```

### 6. Run the Application
```bash
python app.py
```
Visit `http://127.0.0.1:5001` in your web browser.

---

## 📖 Usage Guide

### For Regular Users
1. **Explore:** Navigate to the homepage to see all approved cafes. Use the filter bar to narrow down by ZIP code or Wi-Fi speed.
2. **Plan:** Click "Plan Session" in the navbar, select your activity (e.g., "Heavy Coding"), and get tailored recommendations.
3. **Compare:** Click "Compare Spots", select up to 4 cafes from the dropdowns, and evaluate them side-by-side.
4. **Contribute:** Create an account. Click a cafe to leave a review, or click "+ Add Cafe" to submit a hidden gem you recently discovered.

### For Administrators
1. Navigate to `http://127.0.0.1:5001/admin/login` (or click the shield icon if available).
2. Log in using the credentials defined in your `.env` file.
3. **Dashboard:** Here you can Approve/Revoke newly submitted cafes, process community Verification Reports, and moderate user reviews and replies.

---

## 🧮 Workability Scoring System

The base Workability Score is a weighted average calculated in `models.py`:
* **Wi-Fi Quality:** 25%
* **Power Outlets:** 20%
* **Noise Level:** 20%
* **Seating Comfort:** 15%
* **Affordability:** 10%
* **Opening Hours:** 10%

*Note: These weights shift dynamically when a user utilizes the "Plan Session" feature.*

---

## 🗄️ Database Architecture

* **User:** Handles authentication, password hashing, and relationships to reviews/cafes.
* **Cafe:** Stores core location data, imagery URLs, boolean amenities (backup power), and raw scores.
* **VerificationReport:** Tracks user-submitted corrections to cafe data.
* **Review & ReviewReply:** Handles the nested community feedback system.
* **ReviewVote:** Tracks likes/dislikes on reviews with unique constraints to prevent double-voting.

---

## 🤝 Contributing
Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---
*Built with ❤️ for coders, remote workers, and caffeine enthusiasts.*