# ✈️ PocketRunway (V2)

**PocketRunway** is not an accountant's spreadsheet. It is a financial companion for college students on a fixed monthly allowance. It tells you exactly how much you can spend *today* to survive the month.

No pie charts. No complex analytics. Just a clean, empathy-driven interface that shifts from morning to night to keep you on track.

## ✨ V2 Features
* **The "Safe Today" Engine:** A smart rolling-average algorithm that calculates your daily allowance. If you overspend today, it gracefully reduces your budget for tomorrow.
* **Time-of-Day Theming:** The UI dynamically shifts colors and greetings based on your local time (Morning, Afternoon, Evening, Night) inspired by cozy slice-of-life aesthetics.
* **Tactile UI:** Features a subtle film-grain overlay and OKLCH color palettes to shed the generic "SaaS boilerplate" look.
* **Income & Refunds:** Easily add mid-month top-ups or log IOU settlements without breaking your expense math.
* **5-Day Streaks:** Visual habit-building to show you how well you've stuck to your budget this week.

## 🛠️ Tech Stack
* **Backend:** Python, Flask, Flask-Login
* **Database:** SQLite (via Flask-SQLAlchemy)
* **Frontend:** HTML5, standard JavaScript, and Tailwind CSS (via CDN for zero-build-step rapid prototyping)

## 🚀 Quick Start Guide (For Beginners)

**⚠️ Important:** This application strictly requires **Python 3.12**. Please ensure you have this version installed before proceeding.

**1. Clone the repository**
```bash
git clone [https://github.com/thakurtrishit2005-art/Expense-Tracker.git]
cd Expense-Tracker
```

**2. Create a Virtual Environment (Recommended)**
```bash
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the Application**
```bash
python app.py
```
*The app will automatically create a fresh SQLite database for you. Open your browser and go to `http://127.0.0.1:5000`.*


---
*Designed to stretch the month.*