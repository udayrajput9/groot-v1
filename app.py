from flask import Flask, jsonify, request, render_template, session, redirect
import requests
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from db_setup import init_db
from asteroid_db import search_local, row_to_neo_format, seed_database, get_all_local
from local_model import AsteroidReportGenerator
from google import genai



app = Flask(__name__)
app.secret_key = 'groot_asteroid_tracker_secret_key_2026'

NASA_API_KEY = "rkvsgmB9iKdZx4Usn7rQKe5n2ifd1lPgHWbqdJLM"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'users.db')

init_db(DB_PATH)
print("✅ Database initialized")

# Seed famous asteroids into local KB
try:
    seed_database(verbose=False)
    print("✅ Asteroid Knowledge Base ready")
except Exception as _e:
    print(f"⚠ KB seed warning: {_e}")

# Init report generator
_report_gen = AsteroidReportGenerator()

# ── Email Config (set these as environment variables in production) ────────────
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER",   "groot.spacex@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD",  "gmllmgymnuleuhib")


# ── Welcome Email ─────────────────────────────────────────────────────────────

def send_welcome_email(to_email, username):
    """Send a beautiful HTML welcome email when a new user registers."""

    subject = "🌿 Welcome to GROOT — Your Asteroid Finder!"

    # Plain text fallback
    plain_text = f"""
Hey {username}!

Welcome to GROOT — Your Personal Asteroid Finder! 🌿

We're thrilled to have you on board.

Here's what you can do on GROOT:
  * Track real-time asteroids from NASA
  * See hazard status of near-Earth objects
  * Get asteroid alerts directly to your email
  * Explore interactive space visualization
  * Save your favorite asteroids

Start Exploring: http://localhost:5000/dashboard

Stay curious, stay safe!
— The GROOT Team

© 2026 GROOT - Your Asteroid Finder
"""

    # Beautiful HTML email
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to GROOT</title>
</head>
<body style="margin:0; padding:0; background-color:#0a1428; font-family:'Segoe UI', Arial, sans-serif;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a1428; padding:40px 0;">
    <tr>
      <td align="center">

        <!-- Card -->
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(160deg,#141932 0%,#1e1e50 100%);
                      border-radius:20px;
                      border:1px solid rgba(0,191,255,0.3);
                      box-shadow:0 20px 60px rgba(0,0,0,0.6);
                      overflow:hidden;
                      max-width:600px; width:100%;">

          <!-- Header Banner -->
          <tr>
            <td style="background:linear-gradient(90deg,#0a1428 0%,#1a1a3e 100%);
                       padding:40px 40px 30px; text-align:center;
                       border-bottom:2px solid rgba(0,191,255,0.25);">
              <div style="font-size:52px; margin-bottom:10px;">🌿</div>
              <h1 style="margin:0; font-size:32px; letter-spacing:5px; font-weight:800;
                         background:linear-gradient(90deg,#00ff88,#00ccff);
                         -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                         background-clip:text;">
                GROOT
              </h1>
              <p style="margin:6px 0 0; color:#ffdd57; font-size:14px; letter-spacing:2px;">
                YOUR ASTEROID FINDER
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 44px;">

              <!-- Welcome heading -->
              <h2 style="color:#00ffff; font-size:22px; margin:0 0 6px;">
                Hey {username}! 👋
              </h2>
              <h3 style="color:#ffffff; font-size:18px; font-weight:400; margin:0 0 24px;">
                Welcome aboard — you're officially a Space Explorer! 🚀
              </h3>

              <p style="color:#b0c4de; font-size:15px; line-height:1.7; margin:0 0 28px;">
                We're super excited to have you join <strong style="color:#00ff88;">GROOT</strong>. 
                Your account is all set and the universe is waiting for you to explore it! 
                Here's everything you can do right now:
              </p>

              <!-- Feature Cards -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">

                <tr>
                  <td style="padding:0 0 12px;">
                    <table width="100%" cellpadding="16" cellspacing="0"
                           style="background:rgba(0,191,255,0.07);
                                  border:1px solid rgba(0,191,255,0.2);
                                  border-radius:12px;">
                      <tr>
                        <td style="font-size:26px; width:44px; vertical-align:middle;">🛸</td>
                        <td style="vertical-align:middle;">
                          <div style="color:#00ccff; font-weight:700; font-size:14px; margin-bottom:3px;">
                            Real-Time Asteroid Tracking
                          </div>
                          <div style="color:#8ab0cc; font-size:13px; line-height:1.5;">
                            Live NASA data — see every asteroid passing near Earth today.
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:0 0 12px;">
                    <table width="100%" cellpadding="16" cellspacing="0"
                           style="background:rgba(0,255,136,0.07);
                                  border:1px solid rgba(0,255,136,0.2);
                                  border-radius:12px;">
                      <tr>
                        <td style="font-size:26px; width:44px; vertical-align:middle;">🚨</td>
                        <td style="vertical-align:middle;">
                          <div style="color:#00ff88; font-weight:700; font-size:14px; margin-bottom:3px;">
                            Asteroid Alert Emails
                          </div>
                          <div style="color:#8ab0cc; font-size:13px; line-height:1.5;">
                            We'll email you at <strong style="color:#fff;">{to_email}</strong> whenever 
                            a potentially hazardous asteroid approaches Earth.
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:0 0 12px;">
                    <table width="100%" cellpadding="16" cellspacing="0"
                           style="background:rgba(255,221,87,0.07);
                                  border:1px solid rgba(255,221,87,0.2);
                                  border-radius:12px;">
                      <tr>
                        <td style="font-size:26px; width:44px; vertical-align:middle;">🌌</td>
                        <td style="vertical-align:middle;">
                          <div style="color:#ffdd57; font-weight:700; font-size:14px; margin-bottom:3px;">
                            3D Space Visualization
                          </div>
                          <div style="color:#8ab0cc; font-size:13px; line-height:1.5;">
                            Interactive space dashboard — watch asteroids orbit in real-time.
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <tr>
                  <td style="padding:0 0 4px;">
                    <table width="100%" cellpadding="16" cellspacing="0"
                           style="background:rgba(180,100,255,0.07);
                                  border:1px solid rgba(180,100,255,0.2);
                                  border-radius:12px;">
                      <tr>
                        <td style="font-size:26px; width:44px; vertical-align:middle;">⭐</td>
                        <td style="vertical-align:middle;">
                          <div style="color:#cc99ff; font-weight:700; font-size:14px; margin-bottom:3px;">
                            Save Your Favorites
                          </div>
                          <div style="color:#8ab0cc; font-size:13px; line-height:1.5;">
                            Bookmark asteroids you love and track them over time.
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

              </table>

              <!-- CTA Button -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:30px;">
                <tr>
                  <td align="center">
                    <a href="http://localhost:5000/dashboard"
                       style="display:inline-block;
                              background:linear-gradient(90deg,#00ff88,#00ccff);
                              color:#000; font-weight:800; font-size:16px;
                              padding:16px 44px; border-radius:50px;
                              text-decoration:none; letter-spacing:1px;">
                      🚀 Start Exploring Space
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:0 0 24px;">

              <!-- Fun fact -->
              <table width="100%" cellpadding="20" cellspacing="0"
                     style="background:rgba(255,255,255,0.03);
                            border-radius:12px; margin-bottom:10px;">
                <tr>
                  <td>
                    <p style="color:#ffdd57; font-size:13px; font-weight:700;
                               margin:0 0 8px; letter-spacing:1px;">
                      ☄️ SPACE FACT OF THE DAY
                    </p>
                    <p style="color:#8ab0cc; font-size:13px; line-height:1.6; margin:0;">
                      Over <strong style="color:#fff;">1 million asteroids</strong> are currently tracked 
                      in our solar system — and NASA discovers new ones every single day. 
                      GROOT uses their live data to keep you informed!
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:rgba(0,0,0,0.3); padding:24px 44px;
                       border-top:1px solid rgba(0,191,255,0.15); text-align:center;">
              <p style="color:#00ff88; font-size:16px; margin:0 0 4px;">
                🌿 GROOT — Your Asteroid Finder
              </p>
              <p style="color:#4a6070; font-size:12px; margin:0 0 10px;">
                Making space exploration fun and interactive for everyone.
              </p>
              <p style="color:#4a6070; font-size:11px; margin:0;">
                Real data powered by NASA NEO API &nbsp;|&nbsp; © 2026 GROOT
              </p>
              <p style="color:#2a4050; font-size:11px; margin:8px 0 0;">
                You received this email because you registered on GROOT with this address.
              </p>
            </td>
          </tr>

        </table>
        <!-- / Card -->

      </td>
    </tr>
  </table>

</body>
</html>
"""

    msg = MIMEMultipart('alternative')
    msg['From']    = EMAIL_SENDER
    msg['To']      = to_email
    msg['Subject'] = subject

    # Attach both plain and HTML (email clients pick the best one)
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_body,  'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, to_email, msg.as_string())
            print(f"✅ Welcome email sent to {to_email}")
            return True
    except Exception as e:
        print(f"❌ Welcome email failed: {e}")
        return False


# ── Asteroid Alert Email ──────────────────────────────────────────────────────

def send_alert_email(to_email, asteroid_name, miss_distance_km,
                     velocity_kmh, close_approach_date, close_approach_time, is_hazardous):
    subject      = f"🚨 Asteroid Alert: {asteroid_name} approaching Earth!"
    hazard_label = "⚠️ POTENTIALLY HAZARDOUS" if is_hazardous else "✅ Not Hazardous"
    body = f"""
Hello,
Our system detected a near-Earth asteroid!

ASTEROID: {asteroid_name}
Close Approach Date: {close_approach_date}
Time (UTC): {close_approach_time}
Miss Distance: {float(miss_distance_km):,.0f} km
Velocity: {float(velocity_kmh):,.0f} km/h
Hazard Status: {hazard_label}

Stay curious, stay safe!
— GROOT Asteroid Tracker Team
"""
    msg            = MIMEMultipart()
    msg['From']    = EMAIL_SENDER
    msg['To']      = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, to_email, msg.as_string())
            return True
    except Exception as e:
        print(f"❌ Alert email failed: {e}")
        return False


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == password:
        session['user'] = username

        # ✅ Send today's asteroid digest on every login
        conn2 = sqlite3.connect(DB_PATH)
        c2 = conn2.cursor()
        c2.execute("SELECT email FROM users WHERE username=?", (username,))
        email_row = c2.fetchone()
        conn2.close()
        if email_row:
            thread = threading.Thread(
                target=_dispatch_daily_email,
                args=(email_row[0], username),
                daemon=True
            )
            thread.start()

        return jsonify({"success": True, "redirect": "/dashboard"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return redirect('/login')

    data     = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email    = data.get('email', '').strip()

    if not username or not password or not email:
        return jsonify({'success': False, 'message': 'All fields required'}), 400

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Username already taken. Try another.'}), 400

    c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
              (username, password, email))
    conn.commit()
    conn.close()

    session['user'] = username

    # ✅ Send welcome email in background (won't slow down signup response)
    thread = threading.Thread(
        target=send_welcome_email,
        args=(email, username),
        daemon=True
    )
    thread.start()

    # ✅ Send today's asteroid digest on signup
    thread2 = threading.Thread(
        target=_dispatch_daily_email,
        args=(email, username),
        daemon=True
    )
    thread2.start()

    return jsonify({'success': True, 'redirect': '/dashboard'})


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', username=session['user'])


@app.route('/search')
def search():
    if 'user' not in session:
        return redirect('/login')
    return render_template('search.html')


@app.route('/api/asteroids')
def get_asteroids():
    date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    url  = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={date}&end_date={date}&api_key={NASA_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MISSING ROUTES — Search, AI Insights, Favorites
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 1. Smart Asteroid Search ─────────────────────────────
#  Priority: Local KB first → NASA live fallback
@app.route('/api/search-asteroid')
def search_asteroid():
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400

    # ── Step 1: Search local Knowledge Base first ──────────
    local_rows = search_local(name)
    if local_rows:
        results = [row_to_neo_format(r) for r in local_rows[:5]]
        return jsonify({
            'success': True,
            'source' : 'local_db',
            'results': results,
            'count'  : len(results)
        })

    # ── Step 2: Fallback → NASA NEO browse API ─────────────
    try:
        browse_url = f"https://api.nasa.gov/neo/rest/v1/neo/browse?api_key={NASA_API_KEY}"
        r = requests.get(browse_url, timeout=12)
        all_neos = r.json().get('near_earth_objects', [])
        matched  = [n for n in all_neos if name.lower() in n.get('name','').lower()]

        # Step 3: Fallback → today's feed
        if not matched:
            today    = datetime.today().strftime('%Y-%m-%d')
            feed_url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
            fr       = requests.get(feed_url, timeout=12)
            neos_today = fr.json().get('near_earth_objects', {}).get(today, [])
            matched  = [n for n in neos_today if name.lower() in n.get('name','').lower()]
            if not matched and neos_today:
                matched = neos_today[:3]

        return jsonify({'success': True, 'source': 'nasa_live', 'results': matched[:5], 'count': len(matched)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── 2. Local-Model Report Generator ──────────────────────
#  Generates rich report using local_model.py (no external AI calls)
#  If data came from local KB → uses extra fields (mission, fun_fact, etc.)
@app.route('/api/asteroid-info', methods=['POST'])
def asteroid_info():
    try:
        body = request.get_json()
        if not body:
            return jsonify({'success': False, 'error': 'No data sent'}), 400

        name = body.get('name', 'Unknown')
        data = body.get('data', {})

        # Use local_model AsteroidReportGenerator
        report_text = _report_gen.generate_report(name, data)

        # Extra local-DB metadata to enrich the report
        local_meta = data.get('_local', {})
        extra_sections = []

        if local_meta.get('spectral_type'):
            extra_sections.append(f"🔬 SPECTRAL TYPE: {local_meta['spectral_type']}")
        if local_meta.get('discovery_year'):
            extra_sections.append(f"📅 DISCOVERED: {local_meta['discovery_year']} by {local_meta.get('discovered_by','Unknown')}")
        if local_meta.get('orbital_period'):
            extra_sections.append(f"🔄 ORBITAL PERIOD: {local_meta['orbital_period']:.1f} days ({local_meta['orbital_period']/365.25:.2f} years)")
        if local_meta.get('semi_major_au'):
            extra_sections.append(f"🌌 SEMI-MAJOR AXIS: {local_meta['semi_major_au']:.4f} AU")
        if local_meta.get('eccentricity'):
            extra_sections.append(f"📐 ECCENTRICITY: {local_meta['eccentricity']:.4f}")
        if local_meta.get('inclination'):
            extra_sections.append(f"📏 ORBITAL INCLINATION: {local_meta['inclination']:.2f}°")
        if local_meta.get('mission'):
            extra_sections.append(f"🚀 MISSION: {local_meta['mission']}")
        if local_meta.get('fun_fact'):
            extra_sections.append(f"💡 FUN FACT: {local_meta['fun_fact']}")
        if local_meta.get('nasa_url'):
            extra_sections.append(f"🔗 MORE INFO: {local_meta['nasa_url']}")

        source_label = 'local_kb' if local_meta else 'nasa_live'

        return jsonify({
            'success'      : True,
            'info'         : report_text,
            'extra'        : extra_sections,
            'source'       : source_label,
            'model'        : 'AsteroidReportGenerator v2.0 (local)'
        })

    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500


# ── 2b. List all local KB asteroids ──────────────────────
@app.route('/api/asteroid-kb')
def asteroid_kb_list():
    """Returns all asteroids stored in the local Knowledge Base."""
    try:
        rows = get_all_local()
        summary = [{
            'name'      : r['name'],
            'neo_id'    : r['neo_id'],
            'hazardous' : bool(r.get('is_hazardous',0)),
            'diameter_km': r.get('diameter_max_km'),
            'type'      : r.get('spectral_type'),
            'discovered': r.get('discovery_year'),
            'mission'   : r.get('mission',''),
            'source'    : r.get('source','seeded'),
        } for r in rows]
        return jsonify({'success': True, 'count': len(summary), 'asteroids': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── 3. Dashboard AI Insights ───────────────────────────────
# dashboard.html calls POST /api/dashboard-insights
# This was MISSING → AI Insights section stayed at "Loading..."
@app.route('/api/dashboard-insights', methods=['POST'])
def dashboard_insights():
    try:
        body = request.get_json()
        neos = body.get('asteroids', [])

        if not neos:
            return jsonify({'success': False, 'error': 'No asteroid data'}), 400

        total      = len(neos)
        hazardous  = [n for n in neos if n.get('is_potentially_hazardous_asteroid')]
        safe       = total - len(hazardous)

        # Closest asteroid
        closest = None
        min_dist = float('inf')
        for n in neos:
            ca = n.get('close_approach_data', [{}])
            if ca:
                d = float(ca[0].get('miss_distance', {}).get('kilometers', 1e12) or 1e12)
                if d < min_dist:
                    min_dist = d
                    closest = n

        # Fastest
        fastest = None
        max_vel = 0
        for n in neos:
            ca = n.get('close_approach_data', [{}])
            if ca:
                v = float(ca[0].get('relative_velocity', {}).get('kilometers_per_hour', 0) or 0)
                if v > max_vel:
                    max_vel = v
                    fastest = n

        # Largest
        largest = max(neos, key=lambda n: n.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_max', 0))
        largest_size = largest.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_max', 0)

        # Hazard level summary
        haz_pct = (len(hazardous) / total * 100) if total > 0 else 0
        if haz_pct == 0:    threat_level = "🟢 ALL CLEAR — No hazardous objects today."
        elif haz_pct < 20:  threat_level = f"🟡 LOW ALERT — {len(hazardous)} of {total} objects flagged as potentially hazardous."
        elif haz_pct < 50:  threat_level = f"🟠 MODERATE — {len(hazardous)} hazardous NEOs passing today. Monitoring advised."
        else:               threat_level = f"🔴 HIGH ACTIVITY — {len(hazardous)} of {total} NEOs are potentially hazardous!"

        insights = f"""{threat_level}

📊 Today's Summary: {total} total near-Earth objects detected — {len(hazardous)} hazardous, {safe} safe.

🏆 Closest Pass: {closest['name'] if closest else 'N/A'} at {min_dist/1000:,.0f}k km ({min_dist/384400:.2f} lunar distances).

⚡ Fastest Object: {fastest['name'] if fastest else 'N/A'} at {max_vel:,.0f} km/h ({max_vel/3600:.1f} km/s).

🔭 Largest Object: {largest['name']} — up to {largest_size:.0f} m diameter.

💡 {"⚠️ Stay alert! Multiple hazardous objects are passing today. All are on safe trajectories." if hazardous else "✅ Today is a safe day — all passing asteroids are on trajectories well clear of Earth."}"""

        return jsonify({'success': True, 'insights': insights})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── 4. Favorites API ──────────────────────────────────────
# dashboard.html calls /api/favorites GET / POST / DELETE
# These were all MISSING
@app.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
def favorites():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['user']
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    if request.method == 'GET':
        c.execute('SELECT asteroid_name FROM favorites WHERE username=?', (username,))
        favs = [row[0] for row in c.fetchall()]
        conn.close()
        return jsonify({'success': True, 'favorites': favs})

    elif request.method == 'POST':
        body = request.get_json()
        name = body.get('name', '').strip()
        if not name:
            conn.close()
            return jsonify({'success': False, 'error': 'Name required'}), 400
        # Avoid duplicates
        c.execute('SELECT id FROM favorites WHERE username=? AND asteroid_name=?', (username, name))
        if not c.fetchone():
            c.execute('INSERT INTO favorites (username, asteroid_name) VALUES (?,?)', (username, name))
            conn.commit()
        conn.close()
        return jsonify({'success': True})

    elif request.method == 'DELETE':
        body = request.get_json()
        name = body.get('name', '').strip()
        c.execute('DELETE FROM favorites WHERE username=? AND asteroid_name=?', (username, name))
        conn.commit()
        conn.close()
        return jsonify({'success': True})


@app.route('/visualizer')
def visualizer():
    if 'user' not in session:
        return redirect('/login')
    return render_template('visualizer.html')


@app.route('/api/neo-visual')
def neo_visual():
    """Returns NEO data optimized for 3D visualization."""
    date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    url  = (f"https://api.nasa.gov/neo/rest/v1/feed"
            f"?start_date={date}&end_date={date}&api_key={NASA_API_KEY}")
    try:
        r    = requests.get(url, timeout=12)
        data = r.json()
        neos = data.get('near_earth_objects', {}).get(date, [])
        # Return simplified structure for visualization
        result = []
        for neo in neos:
            ca = neo.get('close_approach_data', [{}])[0]
            result.append({
                'id'        : neo.get('neo_reference_id'),
                'name'      : neo.get('name'),
                'hazardous' : neo.get('is_potentially_hazardous_asteroid', False),
                'diameter_m_min': neo['estimated_diameter']['meters']['estimated_diameter_min'],
                'diameter_m_max': neo['estimated_diameter']['meters']['estimated_diameter_max'],
                'miss_km'   : ca.get('miss_distance', {}).get('kilometers', 0),
                'miss_au'   : ca.get('miss_distance', {}).get('astronomical', 0),
                'miss_ld'   : ca.get('miss_distance', {}).get('lunar', 0),
                'velocity'  : ca.get('relative_velocity', {}).get('kilometers_per_hour', 0),
                'date'      : ca.get('close_approach_date', ''),
            })
        return jsonify({'success': True, 'count': len(result), 'neos': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── 5. Daily Email Subscription API ──────────────────────────────────────────

@app.route('/api/subscribe-daily', methods=['POST'])
def subscribe_daily():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['user']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get user email
    c.execute('SELECT email FROM users WHERE username=?', (username,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'User not found'}), 404
    email = row[0]

    # Upsert subscription
    c.execute('''
        INSERT INTO email_subscriptions (username, email, subscribed)
        VALUES (?, ?, 1)
        ON CONFLICT(username) DO UPDATE SET subscribed=1
    ''', (username,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'subscribed': True, 'message': f'Daily asteroid emails enabled for {email}'})


@app.route('/api/unsubscribe-daily', methods=['POST'])
def unsubscribe_daily():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['user']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO email_subscriptions (username, email, subscribed)
        SELECT ?, email, 0 FROM users WHERE username=?
        ON CONFLICT(username) DO UPDATE SET subscribed=0
    ''', (username, username))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'subscribed': False, 'message': 'Daily emails unsubscribed'})


@app.route('/api/subscription-status')
def subscription_status():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['user']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT subscribed, last_sent_at FROM email_subscriptions WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({'success': True, 'subscribed': bool(row[0]), 'last_sent': row[1]})
    return jsonify({'success': True, 'subscribed': False, 'last_sent': None})


@app.route('/api/send-daily-now', methods=['POST'])
def send_daily_now():
    """Manual trigger — lets a logged-in user receive today's email immediately."""
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['user']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    email = row[0]
    thread = threading.Thread(target=_dispatch_daily_email, args=(email, username), daemon=True)
    thread.start()
    return jsonify({'success': True, 'message': f'Daily email dispatched to {email}'})


# ── Daily Email Engine ────────────────────────────────────────────────────────

def _dispatch_daily_email(to_email, username):
    """Fetches today's NEOs and sends the daily digest email."""
    today = datetime.today().strftime('%Y-%m-%d')
    url = (f"https://api.nasa.gov/neo/rest/v1/feed"
           f"?start_date={today}&end_date={today}&api_key={NASA_API_KEY}")
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        neos = data.get('near_earth_objects', {}).get(today, [])
    except Exception as e:
        print(f"❌ Daily email fetch failed: {e}")
        return False

    if not neos:
        print("⚠ No NEO data for today — skipping daily email")
        return False

    # Sort: hazardous first, then by closest miss distance
    def sort_key(n):
        ca = n.get('close_approach_data', [{}])[0]
        dist = float(ca.get('miss_distance', {}).get('kilometers', 1e12))
        haz = 0 if n.get('is_potentially_hazardous_asteroid') else 1
        return (haz, dist)

    neos_sorted = sorted(neos, key=sort_key)
    ok = send_daily_asteroid_email(to_email, username, today, neos_sorted)

    if ok:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            UPDATE email_subscriptions SET last_sent_at=? WHERE username=?
        ''', (datetime.utcnow().isoformat(), username))
        conn.commit()
        conn.close()
    return ok


def run_scheduled_daily_emails():
    """Called by APScheduler every day at 8 AM — sends to all subscribed users."""
    print(f"📧 Running scheduled daily emails at {datetime.utcnow()}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT s.username, s.email FROM email_subscriptions s
        WHERE s.subscribed=1
    ''')
    subscribers = c.fetchall()
    conn.close()

    if not subscribers:
        print("📭 No subscribers yet.")
        return

    for (username, email) in subscribers:
        _dispatch_daily_email(email, username)
        print(f"  ✅ Sent to {username} <{email}>")


def send_daily_asteroid_email(to_email, username, date_str, neos):
    """Build and send the gorgeous daily asteroid digest HTML email."""

    total     = len(neos)
    hazardous = [n for n in neos if n.get('is_potentially_hazardous_asteroid')]
    safe      = total - len(hazardous)

    # ── Format date nicely
    try:
        dt_nice = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d %Y')
    except Exception:
        dt_nice = date_str

    # ── Subject line
    if hazardous:
        subject = f"🚨 GROOT Daily — {len(hazardous)} Hazardous Asteroid{'s' if len(hazardous)>1 else ''} Passing Today! ({date_str})"
    else:
        subject = f"🌿 GROOT Daily Digest — {total} Asteroids Passing Earth · {date_str}"

    # ── Asteroid row HTML builder
    def asteroid_row(n, index):
        ca   = n.get('close_approach_data', [{}])[0]
        name = n.get('name', 'Unknown').replace('(', '').replace(')', '').strip()
        haz  = n.get('is_potentially_hazardous_asteroid', False)

        try:
            dist_km  = float(ca.get('miss_distance', {}).get('kilometers', 0))
            dist_ld  = float(ca.get('miss_distance', {}).get('lunar', 0))
        except Exception:
            dist_km = dist_ld = 0

        try:
            vel_kmh  = float(ca.get('relative_velocity', {}).get('kilometers_per_hour', 0))
        except Exception:
            vel_kmh  = 0

        try:
            diam_min = float(n['estimated_diameter']['meters']['estimated_diameter_min'])
            diam_max = float(n['estimated_diameter']['meters']['estimated_diameter_max'])
        except Exception:
            diam_min = diam_max = 0

        approach_time = ca.get('close_approach_date_full', ca.get('close_approach_date', 'N/A'))

        if haz:
            badge_bg    = 'rgba(255,60,60,0.18)'
            badge_border= 'rgba(255,60,60,0.5)'
            badge_color = '#ff4444'
            badge_text  = '⚠️ HAZARDOUS'
            row_border  = '1px solid rgba(255,60,60,0.3)'
            row_bg      = 'rgba(255,30,30,0.06)'
            icon        = '☄️'
        else:
            badge_bg    = 'rgba(0,255,136,0.12)'
            badge_border= 'rgba(0,255,136,0.3)'
            badge_color = '#00ff88'
            badge_text  = '✅ SAFE'
            row_border  = '1px solid rgba(0,191,255,0.18)'
            row_bg      = 'rgba(0,191,255,0.04)'
            icon        = '🪨'

        return f"""
        <tr>
          <td style="padding:0 0 12px;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:{row_bg}; border:{row_border}; border-radius:14px; overflow:hidden;">
              <tr>
                <!-- Number badge -->
                <td width="46" style="background:rgba(0,0,0,0.25); text-align:center;
                             vertical-align:top; padding:18px 0; font-size:22px;">{icon}</td>

                <!-- Main info -->
                <td style="padding:16px 18px 14px;">

                  <!-- Name row -->
                  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px;">
                    <tr>
                      <td>
                        <span style="color:#ffffff; font-weight:700; font-size:15px;">{name}</span>
                        &nbsp;
                        <span style="font-size:11px; font-weight:700; letter-spacing:1px;
                                     background:{badge_bg}; color:{badge_color};
                                     border:1px solid {badge_border};
                                     padding:3px 9px; border-radius:20px;">{badge_text}</span>
                      </td>
                      <td align="right">
                        <span style="color:#4a6080; font-size:11px;">#{index}</span>
                      </td>
                    </tr>
                  </table>

                  <!-- Stats grid -->
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td width="25%" style="padding-bottom:6px;">
                        <div style="color:#5a7a99; font-size:10px; letter-spacing:1px; margin-bottom:2px;">MISS DISTANCE</div>
                        <div style="color:#00ccff; font-size:13px; font-weight:700;">{dist_km/1e6:.2f}M km</div>
                        <div style="color:#4a6080; font-size:10px;">{dist_ld:.1f} lunar dist.</div>
                      </td>
                      <td width="25%" style="padding-bottom:6px;">
                        <div style="color:#5a7a99; font-size:10px; letter-spacing:1px; margin-bottom:2px;">VELOCITY</div>
                        <div style="color:#ffdd57; font-size:13px; font-weight:700;">{vel_kmh:,.0f} km/h</div>
                        <div style="color:#4a6080; font-size:10px;">{vel_kmh/3600:.1f} km/s</div>
                      </td>
                      <td width="25%" style="padding-bottom:6px;">
                        <div style="color:#5a7a99; font-size:10px; letter-spacing:1px; margin-bottom:2px;">DIAMETER</div>
                        <div style="color:#cc99ff; font-size:13px; font-weight:700;">{diam_min:.0f}–{diam_max:.0f} m</div>
                        <div style="color:#4a6080; font-size:10px;">{(diam_min+diam_max)/2:.0f} m avg</div>
                      </td>
                      <td width="25%" style="padding-bottom:6px;">
                        <div style="color:#5a7a99; font-size:10px; letter-spacing:1px; margin-bottom:2px;">APPROACH</div>
                        <div style="color:#ff9966; font-size:12px; font-weight:600;">{approach_time}</div>
                      </td>
                    </tr>
                  </table>

                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    # Build all asteroid rows (max 15 to keep email size sane)
    neos_sorted = neos[:15]
    rows_html = ''.join(asteroid_row(n, i+1) for i, n in enumerate(neos_sorted))

    # ── Threat banner
    haz_count = len(hazardous)
    if haz_count == 0:
        threat_bg    = 'rgba(0,255,136,0.1)'
        threat_border= 'rgba(0,255,136,0.3)'
        threat_color = '#00ff88'
        threat_icon  = '🟢'
        threat_text  = f'ALL CLEAR — No hazardous objects detected today. {total} safe asteroids passing Earth.'
    elif haz_count <= 2:
        threat_bg    = 'rgba(255,221,87,0.1)'
        threat_border= 'rgba(255,221,87,0.3)'
        threat_color = '#ffdd57'
        threat_icon  = '🟡'
        threat_text  = f'LOW ALERT — {haz_count} potentially hazardous object{"s" if haz_count>1 else ""} among today\'s {total} NEOs. All on safe trajectories.'
    else:
        threat_bg    = 'rgba(255,60,60,0.1)'
        threat_border= 'rgba(255,60,60,0.4)'
        threat_color = '#ff4444'
        threat_icon  = '🔴'
        threat_text  = f'HIGH ACTIVITY — {haz_count} hazardous asteroids in today\'s {total} NEOs. Monitoring all trajectories.'

    shown_count = len(neos_sorted)
    more_text = f'<p style="text-align:center;color:#4a6080;font-size:12px;margin:4px 0 16px;">+ {total - shown_count} more asteroids not shown</p>' if total > shown_count else ''

    # Plain text fallback
    plain_lines = [f"GROOT Daily Asteroid Digest — {dt_nice}", "=" * 50]
    for i, n in enumerate(neos[:10]):
        ca = n.get('close_approach_data', [{}])[0]
        plain_lines.append(f"{i+1}. {n.get('name','?')} | {'⚠ HAZARDOUS' if n.get('is_potentially_hazardous_asteroid') else '✅ safe'}"
                           f" | {float(ca.get('miss_distance',{}).get('kilometers',0))/1e6:.2f}M km"
                           f" | {float(ca.get('relative_velocity',{}).get('kilometers_per_hour',0)):,.0f} km/h")
    plain_text = "\n".join(plain_lines) + f"\n\nView live dashboard: http://localhost:5000/dashboard\n— GROOT Team"

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GROOT Daily Digest</title>
</head>
<body style="margin:0;padding:0;background:#070d1f;font-family:'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#070d1f;padding:36px 0;">
  <tr><td align="center">

    <table width="640" cellpadding="0" cellspacing="0"
           style="background:linear-gradient(170deg,#0e1530 0%,#171740 60%,#0e1530 100%);
                  border-radius:22px;
                  border:1px solid rgba(0,191,255,0.25);
                  box-shadow:0 24px 80px rgba(0,0,0,0.7);
                  max-width:640px;width:100%;overflow:hidden;">

      <!-- ══ HEADER ══ -->
      <tr>
        <td style="background:linear-gradient(90deg,#050c1e,#111135,#050c1e);
                   padding:36px 40px 28px;text-align:center;
                   border-bottom:2px solid rgba(0,191,255,0.2);">
          <!-- Stars decoration row -->
          <div style="font-size:11px;letter-spacing:8px;color:rgba(0,191,255,0.3);margin-bottom:12px;">★ ✦ ★ ✦ ★</div>
          <div style="font-size:56px;margin-bottom:8px;">🌿</div>
          <h1 style="margin:0;font-size:30px;font-weight:900;letter-spacing:6px;
                     background:linear-gradient(90deg,#00ff88,#00ccff,#cc99ff);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     background-clip:text;">GROOT</h1>
          <p style="margin:4px 0 0;color:#ffdd57;font-size:12px;letter-spacing:3px;font-weight:600;">
            DAILY ASTEROID DIGEST
          </p>
          <p style="margin:10px 0 0;color:rgba(176,196,222,0.7);font-size:13px;">{dt_nice}</p>
        </td>
      </tr>

      <!-- ══ GREETING ══ -->
      <tr>
        <td style="padding:28px 40px 0;">
          <h2 style="margin:0 0 8px;color:#00ccff;font-size:18px;">Hey {username}! 👋</h2>
          <p style="margin:0;color:#8ab0cc;font-size:14px;line-height:1.7;">
            Here's your daily space briefing. NASA tracked <strong style="color:#fff;">{total} near-Earth objects</strong>
            passing by today — <strong style="color:#ff4444;">{len(hazardous)} hazardous</strong> and
            <strong style="color:#00ff88;">{safe} safe</strong>.
          </p>
        </td>
      </tr>

      <!-- ══ THREAT BANNER ══ -->
      <tr>
        <td style="padding:20px 40px 4px;">
          <table width="100%" cellpadding="18" cellspacing="0"
                 style="background:{threat_bg};border:1px solid {threat_border};border-radius:14px;">
            <tr>
              <td style="font-size:22px;width:36px;vertical-align:middle;">{threat_icon}</td>
              <td style="color:{threat_color};font-size:13px;font-weight:700;vertical-align:middle;">{threat_text}</td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- ══ QUICK STATS ══ -->
      <tr>
        <td style="padding:18px 40px 8px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td width="33%" style="text-align:center;padding:14px 8px;
                  background:rgba(0,191,255,0.07);border:1px solid rgba(0,191,255,0.15);
                  border-radius:12px;margin-right:8px;">
                <div style="color:#00ccff;font-size:26px;font-weight:800;">{total}</div>
                <div style="color:#5a7a99;font-size:11px;letter-spacing:1px;margin-top:3px;">TOTAL NEOs</div>
              </td>
              <td width="4px"></td>
              <td width="33%" style="text-align:center;padding:14px 8px;
                  background:rgba(255,60,60,0.07);border:1px solid rgba(255,60,60,0.2);
                  border-radius:12px;">
                <div style="color:#ff4444;font-size:26px;font-weight:800;">{len(hazardous)}</div>
                <div style="color:#5a7a99;font-size:11px;letter-spacing:1px;margin-top:3px;">HAZARDOUS</div>
              </td>
              <td width="4px"></td>
              <td width="33%" style="text-align:center;padding:14px 8px;
                  background:rgba(0,255,136,0.07);border:1px solid rgba(0,255,136,0.15);
                  border-radius:12px;">
                <div style="color:#00ff88;font-size:26px;font-weight:800;">{safe}</div>
                <div style="color:#5a7a99;font-size:11px;letter-spacing:1px;margin-top:3px;">SAFE</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- ══ SECTION TITLE ══ -->
      <tr>
        <td style="padding:22px 40px 10px;">
          <p style="margin:0;color:#4a6080;font-size:11px;font-weight:700;letter-spacing:2px;">
            ☄️ TODAY'S ASTEROID LIST — SORTED BY HAZARD & PROXIMITY
          </p>
          <hr style="border:none;border-top:1px solid rgba(0,191,255,0.1);margin:8px 0 0;">
        </td>
      </tr>

      <!-- ══ ASTEROID ROWS ══ -->
      <tr>
        <td style="padding:0 40px 4px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            {rows_html}
          </table>
          {more_text}
        </td>
      </tr>

      <!-- ══ CTA ══ -->
      <tr>
        <td style="padding:8px 40px 32px;text-align:center;">
          <a href="http://localhost:5000/dashboard"
             style="display:inline-block;
                    background:linear-gradient(90deg,#00ff88,#00ccff);
                    color:#050c1e;font-weight:800;font-size:15px;
                    padding:15px 42px;border-radius:50px;
                    text-decoration:none;letter-spacing:1px;
                    box-shadow:0 4px 20px rgba(0,255,136,0.3);">
            🚀 Open Live Dashboard
          </a>
        </td>
      </tr>

      <!-- ══ FOOTER ══ -->
      <tr>
        <td style="background:rgba(0,0,0,0.35);padding:22px 40px;
                   border-top:1px solid rgba(0,191,255,0.12);text-align:center;">
          <p style="color:#00ff88;font-size:14px;margin:0 0 4px;font-weight:700;">🌿 GROOT — Your Asteroid Finder</p>
          <p style="color:#3a5060;font-size:11px;margin:0 0 8px;">Real data powered by NASA NEO API · © 2026 GROOT</p>
          <p style="color:#2a3a48;font-size:11px;margin:0;">
            You're receiving this because you subscribed to daily digests.
            <a href="http://localhost:5000/dashboard" style="color:#3a6080;">Manage subscription</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    msg = MIMEMultipart('alternative')
    msg['From']    = EMAIL_SENDER
    msg['To']      = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(html_body,  'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_SENDER, to_email, msg.as_string())
            print(f"✅ Daily digest sent to {to_email}")
            return True
    except Exception as e:
        print(f"❌ Daily digest failed for {to_email}: {e}")
        return False


# ── GROOT Chatbot (Gemini AI) ─────────────────────────────────────────────────

import re
from flask_cors import CORS

# ── Blockchain / Web3 Imports ─────────────────────────────────────────────────
import secrets
import hashlib
from eth_account import Account
from eth_account.messages import encode_defunct


# ── Gemini Client (DIRECT API KEY) ──────────────────────────
client = genai.Client(
    api_key="AIzaSyB_HOy4X9B65FGsA2zMilQFbHgKwRbjq7A"
)

MODEL_NAME = "gemini-3-flash-preview"

# ── Local replies ───────────────────────────────────────────
_LOCAL_RESPONSES = {
    r'\b(hi|hello|hey|hii+|helo)\b':
        "Hey there, space explorer! 🌿 I'm GROOT, your asteroid buddy!",
    r'\b(thanks?|thank you|thx|ty)\b':
        "You're welcome! 🚀 Always here to help!",
    r'\b(bye|goodbye|see ya|cya)\b':
        "Goodbye! 🌌 Come back soon!",
    r'\b(who are you|introduce yourself)\b':
        "I'm GROOT 🌿 — your AI-powered asteroid assistant!",
    r'\b(help|what can you do)\b':
        "I help with ☄️ asteroids, 🌍 space science & NASA data!",
}

def get_local_reply(message: str):
    msg = message.lower().strip()
    for pattern, reply in _LOCAL_RESPONSES.items():
        if re.search(pattern, msg):
            return reply
    return None

# ── Chat API ────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"reply": "Please type something 🌿"})

    # 1️⃣ Local response
    local_reply = get_local_reply(user_message)
    if local_reply:
        return jsonify({"reply": local_reply, "source": "local"})

    # 2️⃣ Gemini SDK call
    system_prompt = (
        "You are GROOT, a friendly AI assistant for an asteroid tracking web app. "
        "You specialize in asteroids, space science, NASA data, and near-Earth objects. "
        "Keep answers concise, fun, and space-themed. Use emojis occasionally."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"{system_prompt}\n\nUser: {user_message}"
        )

        return jsonify({
            "reply": response.text,
            "source": "gemini"
        })

    except Exception as e:
        print("Gemini SDK error:", e)
        return jsonify({
            "reply": "Oops! My space antenna failed 🛸 Try again later!",
            "source": "error"
        })

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BLOCKCHAIN AUTH ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _hash_ip(ip):
    """One-way hash an IP for privacy-safe audit logging."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _log_blockchain_action(username, wallet_address, action, ip=None, tx_hash=None, block_data=None):
    """Write a tamper-evident audit log entry to the DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO blockchain_audit_log
            (username, wallet_address, action, tx_hash, block_data, ip_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        username,
        wallet_address,
        action,
        tx_hash,
        block_data,
        _hash_ip(ip) if ip else None
    ))
    conn.commit()
    conn.close()


# ── 1. Generate nonce for wallet login ──────────────────────
@app.route('/api/auth/nonce', methods=['POST'])
def auth_nonce():
    """
    Step 1 of wallet login: client sends wallet address,
    server returns a one-time nonce to sign.
    """
    data = request.get_json(silent=True) or {}
    wallet = (data.get('wallet_address') or '').strip().lower()

    if not wallet or not wallet.startswith('0x') or len(wallet) != 42:
        return jsonify({'success': False, 'error': 'Invalid wallet address'}), 400

    nonce = secrets.token_hex(16)
    message = f"Sign this message to login to GROOT Asteroid Finder.\n\nNonce: {nonce}\n\nThis request will not trigger a blockchain transaction or cost any gas."

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO wallet_nonces (wallet_address, nonce, created_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(wallet_address) DO UPDATE SET nonce=excluded.nonce, created_at=excluded.created_at
    ''', (wallet, nonce))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'nonce': nonce, 'message': message})


# ── 2. Verify signature & create session ────────────────────
@app.route('/api/auth/verify', methods=['POST'])
def auth_verify():
    """
    Step 2 of wallet login: client sends signed message.
    Server verifies the signature, then logs in or registers the user.
    """
    data = request.get_json(silent=True) or {}
    wallet    = (data.get('wallet_address') or '').strip().lower()
    signature = (data.get('signature') or '').strip()
    email     = (data.get('email') or '').strip()   # optional, for new users

    if not wallet or not signature:
        return jsonify({'success': False, 'error': 'wallet_address and signature required'}), 400

    # Fetch stored nonce
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT nonce, created_at FROM wallet_nonces WHERE wallet_address=?', (wallet,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({'success': False, 'error': 'No nonce found. Request a new one.'}), 400

    nonce, created_at = row

    # Reconstruct exact message that was signed
    message = f"Sign this message to login to GROOT Asteroid Finder.\n\nNonce: {nonce}\n\nThis request will not trigger a blockchain transaction or cost any gas."

    # ── Verify the signature cryptographically ──────────────
    try:
        msg_hash = encode_defunct(text=message)
        recovered = Account.recover_message(msg_hash, signature=signature)
        if recovered.lower() != wallet:
            _log_blockchain_action(None, wallet, 'LOGIN_FAILED_SIG', ip=request.remote_addr)
            return jsonify({'success': False, 'error': 'Signature verification failed'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': f'Signature error: {str(e)}'}), 400

    # ── Invalidate used nonce ────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM wallet_nonces WHERE wallet_address=?', (wallet,))

    # ── Find or create user linked to this wallet ────────────
    username = f"wallet_{wallet[2:8]}"   # e.g. wallet_a1b2c3
    c.execute('SELECT username, email FROM users WHERE username=?', (username,))
    user_row = c.fetchone()

    if not user_row:
        # New wallet-based user registration
        user_email = email if email else f"{username}@wallet.groot"
        c.execute('INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)',
                  (username, f'WALLET_AUTH_{wallet}', user_email))
        action = 'WALLET_SIGNUP'
    else:
        user_email = user_row[1]
        action = 'WALLET_LOGIN'

    # ── Check premium status ────────────────────────────────
    c.execute('SELECT is_premium FROM premium_wallets WHERE wallet_address=?', (wallet,))
    prem_row = c.fetchone()
    is_premium = bool(prem_row and prem_row[0]) if prem_row else False

    # Upsert premium_wallets record
    c.execute('''
        INSERT INTO premium_wallets (username, wallet_address, is_premium)
        VALUES (?, ?, ?)
        ON CONFLICT(wallet_address) DO UPDATE SET username=excluded.username
    ''', (username, wallet, 1 if is_premium else 0))

    conn.commit()
    conn.close()

    # ── Blockchain-style immutable audit entry ───────────────
    block_data = f'{{"wallet":"{wallet}","action":"{action}","timestamp":"{datetime.utcnow().isoformat()}"}}'
    _log_blockchain_action(username, wallet, action, ip=request.remote_addr, block_data=block_data)

    # ── Set Flask session ────────────────────────────────────
    session['user']       = username
    session['wallet']     = wallet
    session['is_premium'] = is_premium
    session['auth_method'] = 'wallet'

    return jsonify({
        'success':    True,
        'username':   username,
        'wallet':     wallet,
        'is_premium': is_premium,
        'action':     action,
        'redirect':   '/dashboard'
    })


# ── 3. Blockchain Audit Log viewer ──────────────────────────
@app.route('/api/blockchain/audit-log')
def blockchain_audit_log():
    """Returns the immutable audit log for the logged-in user."""
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    username = session['user']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, wallet_address, action, tx_hash, block_data, ip_hash, timestamp
        FROM blockchain_audit_log
        WHERE username=?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (username,))
    rows = c.fetchall()
    conn.close()

    log = [{
        'id':             r[0],
        'wallet_address': r[1],
        'action':         r[2],
        'tx_hash':        r[3],
        'block_data':     r[4],
        'ip_hash':        r[5],
        'timestamp':      r[6],
    } for r in rows]

    return jsonify({'success': True, 'log': log, 'count': len(log)})


# ── 4. Check premium / token-gate status ────────────────────
@app.route('/api/blockchain/premium-status')
def premium_status():
    """
    Returns whether the logged-in wallet is premium.
    In production: call an ERC-20 / ERC-721 contract here.
    """
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    wallet = session.get('wallet')
    if not wallet:
        return jsonify({'success': True, 'is_premium': False, 'reason': 'no_wallet_linked'})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT is_premium, verified_at FROM premium_wallets WHERE wallet_address=?', (wallet,))
    row = c.fetchone()
    conn.close()

    is_premium  = bool(row and row[0])
    verified_at = row[1] if row else None

    return jsonify({
        'success':     True,
        'is_premium':  is_premium,
        'wallet':      wallet,
        'verified_at': verified_at,
        'note': 'Connect an ERC-20/ERC-721 token contract here for real token-gating in production.'
    })


# ── 5. Grant premium (demo endpoint — lock down in production) ──
@app.route('/api/blockchain/grant-premium', methods=['POST'])
def grant_premium():
    """Demo: manually grant premium to a wallet. In production replace with on-chain token check."""
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    wallet = session.get('wallet')
    if not wallet:
        return jsonify({'success': False, 'error': 'No wallet linked to this session'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE premium_wallets SET is_premium=1, verified_at=datetime("now") WHERE wallet_address=?', (wallet,))
    conn.commit()
    conn.close()

    session['is_premium'] = True
    _log_blockchain_action(session['user'], wallet, 'PREMIUM_GRANTED', ip=request.remote_addr)

    return jsonify({'success': True, 'is_premium': True, 'wallet': wallet})


# ── APScheduler: fire daily at 08:00 UTC ─────────────────────────────────────
_scheduler = BackgroundScheduler(timezone='UTC')
_scheduler.add_job(run_scheduled_daily_emails, 'cron', hour=8, minute=0, id='daily_digest')
_scheduler.start()
print("⏰ Daily email scheduler started — fires every day at 08:00 UTC")


if __name__ == '__main__':
    app.run(debug=True)
