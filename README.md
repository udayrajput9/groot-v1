# 🌿 GROOT — Your Asteroid Finder

> **Real-time Near-Earth Object tracker powered by NASA NEO API, 3D solar system visualization, AI-powered insights, and daily email digests.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?style=flat-square&logo=flask)
![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=flat-square&logo=three.js)
![NASA API](https://img.shields.io/badge/NASA-NEO%20API-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📸 Features

| Feature | Description |
|---|---|
| 🛸 **Live Asteroid Feed** | Fetches today's Near-Earth Objects directly from NASA's NEO API |
| 🌌 **3D Solar System** | Interactive Three.js visualization with realistic orbits, rocky asteroid geometry, and planetary motion |
| 🔭 **Smart Search** | Searches a local Knowledge Base first, then falls back to live NASA data |
| 🤖 **AI Insights** | Local model generates detailed reports for each asteroid — no external AI calls |
| 📧 **Daily Email Digest** | Beautiful HTML email with today's full asteroid list sent every morning at 8 AM UTC |
| ⭐ **Favorites** | Save and track your favourite asteroids per user account |
| 🚨 **Hazard Alerts** | Automatic detection and flagging of potentially hazardous asteroids |
| 📱 **Fully Responsive** | Works on desktop, tablet, and mobile |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/groot.git
cd groot
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

Create a `.env` file in the root directory:

```env
EMAIL_SENDER=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

> **Note:** Use a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password. 2-Step Verification must be enabled on your Google account.

### 5. Run the app

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
groot/
├── app.py                  # Main Flask application, routes, email logic, scheduler
├── db_setup.py             # SQLite schema — users, favorites, subscriptions
├── asteroid_db.py          # Local Knowledge Base — search & seed functions
├── local_model.py          # Asteroid report generator (no external AI)
├── nasa_data.py            # NASA NEO API helpers
├── requirements.txt        # Python dependencies
├── users.db                # SQLite database (auto-created on first run)
│
├── templates/
│   ├── landing.html        # Public landing page
│   ├── login.html          # Login & signup page
│   ├── dashboard.html      # Main user dashboard
│   ├── search.html         # Asteroid search page
│   └── visualizer.html     # 3D solar system visualizer
│
└── static/
    ├── landing.css
    └── landing.js
```

---

## 🌌 3D Visualizer

The visualizer is built with **Three.js r128** and features:

- ☀️ Sun with animated corona glow
- 🌍 Mercury, Venus, Earth, Mars with realistic orbital speeds
- 🌙 Moon orbiting Earth
- ☄️ Each NEO rendered as a jagged rocky mesh with its own visible orbit path
- 🔴 Hazardous asteroids highlighted with a pulsing red ring
- 🎯 Click any asteroid to inspect it; zoom in with the focus button
- 🖱️ Drag to rotate · Scroll to zoom · `R` to reset view

---

## 📧 Email System

GROOT sends two types of emails:

### Welcome Email
Sent automatically when a new user registers. Contains feature overview and a link to the dashboard.

### Daily Digest
A fully designed HTML email with:
- Threat level banner (🟢 All Clear / 🟡 Low Alert / 🔴 High Activity)
- Quick stats (Total NEOs, Hazardous, Safe)
- Full asteroid list sorted by hazard status and proximity
- Each asteroid shows: miss distance, velocity, estimated diameter, and approach time

**Schedule:** Every day at **8:00 AM UTC** via APScheduler.

Users can also:
- Subscribe / Unsubscribe from the dashboard
- Trigger an immediate send with the **"Send Today's Email Now"** button

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/asteroids?date=YYYY-MM-DD` | Fetch NEOs for a date |
| `GET` | `/api/search-asteroid?name=...` | Search by name (KB → NASA fallback) |
| `POST` | `/api/asteroid-info` | Generate AI report for an asteroid |
| `GET` | `/api/asteroid-kb` | List all local KB asteroids |
| `POST` | `/api/dashboard-insights` | Get AI summary of today's NEOs |
| `GET/POST/DELETE` | `/api/favorites` | Manage user favorites |
| `POST` | `/api/subscribe-daily` | Subscribe to daily emails |
| `POST` | `/api/unsubscribe-daily` | Unsubscribe from daily emails |
| `GET` | `/api/subscription-status` | Check subscription state |
| `POST` | `/api/send-daily-now` | Trigger immediate daily email |

---

## 🛠️ Tech Stack

**Backend**
- [Flask](https://flask.palletsprojects.com/) — web framework
- [APScheduler](https://apscheduler.readthedocs.io/) — daily email cron job
- SQLite — user data, favorites, subscriptions
- smtplib — email delivery via Gmail SMTP

**Frontend**
- [Three.js r128](https://threejs.org/) — 3D visualization
- Google Fonts — Orbitron, Rajdhani, Comfortaa, Montserrat
- Vanilla JS — no frontend framework

**Data**
- [NASA NEO API](https://api.nasa.gov/) — live asteroid feed

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `EMAIL_SENDER` | `groot.spacex@gmail.com` | Gmail address to send from |
| `EMAIL_PASSWORD` | *(set in `.env`)* | Gmail App Password |
| `NASA_API_KEY` | *(in app.py)* | NASA API key — get a free key at [api.nasa.gov](https://api.nasa.gov/) |

---

## 📦 Dependencies

```
Flask
Flask-Cors
requests
numpy
pandas
scikit-learn
joblib
SQLAlchemy
python-dotenv
Werkzeug
gunicorn
apscheduler
```

---

## 🚢 Deployment

### Gunicorn (Linux/macOS)

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

### Docker (optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

> **Remember** to update the dashboard URL from `http://localhost:5000` to your production domain in the email templates inside `app.py`.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [NASA Open APIs](https://api.nasa.gov/) for the NEO data
- [Three.js](https://threejs.org/) for 3D rendering
- [APScheduler](https://apscheduler.readthedocs.io/) for job scheduling

---

<p align="center">Made with ☄️ and 🌿 by the GROOT Team</p>
