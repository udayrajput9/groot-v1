from flask import Flask, jsonify, request, render_template, session, redirect
import requests
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import threading
from db_setup import init_db
from asteroid_db import search_local, row_to_neo_format, seed_database, get_all_local
from local_model import AsteroidReportGenerator

app = Flask(__name__)
app.secret_key = 'groot_asteroid_tracker_secret_key_2026'

NASA_API_KEY = "#"

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
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER",   "#")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD",  "#")


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

if __name__ == '__main__':
    app.run(debug=True)
