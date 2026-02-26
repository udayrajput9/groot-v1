# 🌿 GROOT — Your Asteroid Finder

> **Real-time Near-Earth Object tracker powered by NASA NEO API, 3D solar system visualization, AI-powered insights, daily email digests, and blockchain-secured authentication.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?style=flat-square&logo=flask)
![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=flat-square&logo=three.js)
![NASA API](https://img.shields.io/badge/NASA-NEO%20API-blue?style=flat-square)
![Blockchain](https://img.shields.io/badge/Auth-Blockchain%20%2F%20MetaMask-orange?style=flat-square&logo=ethereum)
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
| ⛓️ **Blockchain Auth** | MetaMask wallet login with cryptographic signature verification — no password needed |
| 🔐 **Immutable Audit Log** | Every login is recorded in a tamper-proof on-chain-style audit log with hashed IPs |
| 🪙 **Token-Gated Premium** | Premium features unlockable via connected wallet (ERC-20/NFT contract-ready) |
| 📱 **Fully Responsive** | Works on desktop, tablet, and mobile |

---

## ⛓️ Blockchain Integration (v2 — New)

GROOT v2 introduces four layers of blockchain-based security and identity directly into the authentication system.

### 1. 🦊 MetaMask Wallet Login

Users can now sign in using their Ethereum wallet — **no username or password required**. The flow is:

1. User clicks **"Connect MetaMask"** on the login page
2. Server generates a one-time cryptographic **nonce** tied to the wallet address
3. MetaMask asks the user to **sign** a human-readable challenge message (no transaction, no gas)
4. Server uses `eth_account` to **verify the signature** and recover the signer's address
5. If it matches, a Flask session is created — the user is logged in or auto-registered

This means identity is proven by **cryptographic private key ownership**, not by a password that could be leaked or guessed.

### 2. 📜 Immutable Blockchain Audit Log

Every authentication event is written to a tamper-evident audit log (`blockchain_audit_log` table) with:

- The wallet address (or username for classic login)
- The action type (`WALLET_LOGIN`, `WALLET_SIGNUP`, `LOGIN_FAILED_SIG`, `PREMIUM_GRANTED`)
- A JSON block data payload with timestamp — structured like a blockchain transaction record
- A **one-way SHA-256 hash of the IP address** (privacy-safe, non-reversible)

Users can view their personal audit log at any time from the **blockchain panel** in the bottom-left corner of the dashboard.

### 3. 🪙 Token-Gated Premium Features

The system tracks whether a connected wallet has **premium status** via the `premium_wallets` table. In production, replace the demo grant endpoint with a live on-chain check against any ERC-20 token balance or ERC-721 NFT ownership. The dashboard shows a **Premium Wallet** badge for premium users.

### 4. 🔑 Passwordless Architecture

Wallet-authenticated users are stored in the `users` table with a non-usable sentinel password (`WALLET_AUTH_0x…`). They can only ever log in via their wallet — eliminating the password-leak attack surface entirely for wallet users.

---

### ⛓️ Blockchain API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/nonce` | Generate a one-time challenge nonce for a wallet address |
| `POST` | `/api/auth/verify` | Verify MetaMask signature and create authenticated session |
| `GET` | `/api/blockchain/audit-log` | Fetch the immutable login audit log for the current user |
| `GET` | `/api/blockchain/premium-status` | Check if the connected wallet has premium access |
| `POST` | `/api/blockchain/grant-premium` | Grant premium to the current wallet (demo — replace with on-chain check in production) |

---

### 🗄️ New Database Tables (v2)

```sql
-- Stores one-time nonces for wallet challenge-response auth
wallet_nonces (
    wallet_address TEXT PRIMARY KEY,
    nonce          TEXT NOT NULL,
    created_at     TEXT
)

-- Immutable audit log — every auth event recorded here
blockchain_audit_log (
    id             INTEGER PRIMARY KEY,
    username       TEXT,
    wallet_address TEXT,
    action         TEXT,      -- WALLET_LOGIN | WALLET_SIGNUP | LOGIN_FAILED_SIG | PREMIUM_GRANTED
    tx_hash        TEXT,
    block_data     TEXT,      -- JSON payload structured like a blockchain transaction
    ip_hash        TEXT,      -- SHA-256 hash of IP address (privacy-safe)
    timestamp      TEXT
)

-- Premium wallet registry (ERC-20 / NFT hook-in point)
premium_wallets (
    id             INTEGER PRIMARY KEY,
    username       TEXT,
    wallet_address TEXT UNIQUE,
    is_premium     INTEGER DEFAULT 0,
    verified_at    TEXT
)
```

---

### 🔮 Production Upgrade — Real Token Gating

To connect real on-chain token gating, replace the body of the `grant_premium` route with:

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_INFURA_KEY"))
contract = w3.eth.contract(address=YOUR_TOKEN_CONTRACT_ADDRESS, abi=ERC20_ABI)
balance = contract.functions.balanceOf(wallet_address).call()
is_premium = balance > 0   # or > some minimum threshold
```

---

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

> The `eth-account` and `web3` packages are included and required for blockchain authentication.

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

To use **wallet login**, install [MetaMask](https://metamask.io/download/) as a browser extension and connect any Ethereum account.

---

## 📁 Project Structure

```
groot/
├── app.py                  # Main Flask app — routes, email logic, scheduler, blockchain auth
├── db_setup.py             # SQLite schema — users, favorites, subscriptions, blockchain tables
├── asteroid_db.py          # Local Knowledge Base — search & seed functions
├── local_model.py          # Asteroid report generator (no external AI)
├── nasa_data.py            # NASA NEO API helpers
├── requirements.txt        # Python dependencies (includes eth-account, web3)
├── users.db                # SQLite database (auto-created on first run)
│
├── templates/
│   ├── landing.html        # Public landing page
│   ├── login.html          # Login & signup (classic + MetaMask wallet login)  ← updated v2
│   ├── dashboard.html      # Main user dashboard (+ blockchain audit log panel) ← updated v2
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

## 🔑 API Reference

### Core Asteroid

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/asteroids?date=YYYY-MM-DD` | Fetch NEOs for a date |
| `GET` | `/api/search-asteroid?name=...` | Search by name (KB → NASA fallback) |
| `POST` | `/api/asteroid-info` | Generate AI report for an asteroid |
| `GET` | `/api/asteroid-kb` | List all local KB asteroids |
| `POST` | `/api/dashboard-insights` | Get AI summary of today's NEOs |
| `GET/POST/DELETE` | `/api/favorites` | Manage user favorites |

### Email Subscription

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/subscribe-daily` | Subscribe to daily emails |
| `POST` | `/api/unsubscribe-daily` | Unsubscribe from daily emails |
| `GET` | `/api/subscription-status` | Check subscription state |
| `POST` | `/api/send-daily-now` | Trigger immediate daily email |

### ⛓️ Blockchain Auth (v2 — New)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/nonce` | Generate one-time nonce for wallet challenge |
| `POST` | `/api/auth/verify` | Verify MetaMask signature & create session |
| `GET` | `/api/blockchain/audit-log` | View immutable login audit log |
| `GET` | `/api/blockchain/premium-status` | Check wallet premium status |
| `POST` | `/api/blockchain/grant-premium` | Grant premium to wallet (demo) |

---

## 🛠️ Tech Stack

**Backend**
- [Flask](https://flask.palletsprojects.com/) — web framework
- [APScheduler](https://apscheduler.readthedocs.io/) — daily email cron job
- [eth-account](https://eth-account.readthedocs.io/) — Ethereum signature verification *(new v2)*
- [web3.py](https://web3py.readthedocs.io/) — blockchain utilities & contract interaction *(new v2)*
- SQLite — user data, favorites, subscriptions, blockchain audit log
- smtplib — email delivery via Gmail SMTP

**Frontend**
- [Three.js r128](https://threejs.org/) — 3D visualization
- [MetaMask](https://metamask.io/) — Ethereum wallet browser extension *(new v2)*
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
google-genai
eth-account     # Ethereum signature verification (new v2)
web3            # Blockchain utilities (new v2)
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

## 📄 Changelog

### v2.0 — Blockchain Auth Update
- ⛓️ Added MetaMask / Ethereum wallet login (passwordless, signature-based)
- 🔐 Added immutable blockchain-style audit log for all auth events with hashed IPs
- 🪙 Added token-gated premium wallet system (ERC-20/NFT contract-ready)
- 🗄️ Added 3 new database tables: `wallet_nonces`, `blockchain_audit_log`, `premium_wallets`
- 📊 Added blockchain audit log panel widget on the dashboard
- 📦 Added `eth-account` and `web3` to dependencies
- 🔒 Wallet users stored with non-usable sentinel passwords (passwordless by design)

### v1.0 — Initial Release
- 🛸 Live NASA NEO asteroid feed
- 🌌 3D solar system visualizer (Three.js)
- 🤖 Local AI-powered asteroid reports
- 📧 Daily HTML email digest via APScheduler (8 AM UTC)
- ⭐ Per-user favorites system
- 🚨 Hazard alert emails

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [NASA Open APIs](https://api.nasa.gov/) for the NEO data
- [Three.js](https://threejs.org/) for 3D rendering
- [APScheduler](https://apscheduler.readthedocs.io/) for job scheduling
- [MetaMask](https://metamask.io/) for Ethereum wallet integration
- [eth-account](https://eth-account.readthedocs.io/) for cryptographic signature verification

---

<p align="center">Made with ☄️ and ⛓️ by the GROOT Team</p>
