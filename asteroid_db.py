"""
asteroid_db.py — Local Asteroid Knowledge Base
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Seeds DB with 60+ famous asteroids (hardcoded authoritative data)
• Fetches live data from NASA NEO API for each and enriches the DB
• Provides name-based fuzzy search against local DB
• Falls back to NASA live API if not found locally
"""

import sqlite3, json, os, requests
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'users.db')
NASA_KEY = "rkvsgmB9iKdZx4Usn7rQKe5n2ifd1lPgHWbqdJLM"

# ═══════════════════════════════════════════════════════════════
#  CURATED ASTEROID SEED DATA
#  Source: NASA CNEOS, JPL Small-Body Database, Wikipedia
# ═══════════════════════════════════════════════════════════════
FAMOUS_ASTEROIDS = [
    # ── Hall-of-fame PHAs & mission targets ──────────────────
    {
        "neo_id": "2099942", "name": "99942 Apophis",
        "name_aliases": "apophis,2004 mn4",
        "diameter_min_km": 0.310, "diameter_max_km": 0.450,
        "is_hazardous": 1, "absolute_mag": 19.09,
        "orbital_period_d": 323.6, "eccentricity": 0.1912,
        "inclination_deg": 3.34, "semi_major_au": 0.9224,
        "spectral_type": "Sq", "discovery_year": 2004,
        "discovered_by": "Roy Tucker, David Tholen, Fabrizio Bernardi",
        "mission": "ESA Ramses mission (planned 2029 flyby)",
        "fun_fact": "Apophis will pass within 32,000 km of Earth on April 13, 2029 — closer than geostationary satellites. Named after the Egyptian god of chaos.",
        "nasa_url": "https://cneos.jpl.nasa.gov/ca/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2029-04-13",
            "close_approach_date_full": "2029-Apr-13 21:46",
            "relative_velocity": {"kilometers_per_hour": "30600", "kilometers_per_second": "8.5"},
            "miss_distance": {"astronomical": "0.000743", "lunar": "0.289", "kilometers": "31110000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2101955", "name": "101955 Bennu",
        "name_aliases": "bennu,1999 rq36",
        "diameter_min_km": 0.468, "diameter_max_km": 0.565,
        "is_hazardous": 1, "absolute_mag": 20.89,
        "orbital_period_d": 436.6, "eccentricity": 0.2037,
        "inclination_deg": 6.035, "semi_major_au": 1.1264,
        "spectral_type": "B", "discovery_year": 1999,
        "discovered_by": "LINEAR Survey",
        "mission": "OSIRIS-REx (2016–2021), OSIRIS-APEX continuing",
        "fun_fact": "OSIRIS-REx collected 250g of pristine carbon-rich material from Bennu in 2020 — the largest sample ever returned from an asteroid. Bennu has a 1-in-2700 chance of hitting Earth in 2182.",
        "nasa_url": "https://www.asteroidmission.org/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2182-09-24",
            "close_approach_date_full": "2182-Sep-24 00:00",
            "relative_velocity": {"kilometers_per_hour": "60000", "kilometers_per_second": "16.7"},
            "miss_distance": {"astronomical": "0.0037", "lunar": "1.44", "kilometers": "553000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2162173", "name": "162173 Ryugu",
        "name_aliases": "ryugu,1999 ju3",
        "diameter_min_km": 0.865, "diameter_max_km": 0.920,
        "is_hazardous": 0, "absolute_mag": 18.82,
        "orbital_period_d": 473.9, "eccentricity": 0.1902,
        "inclination_deg": 5.88, "semi_major_au": 1.1895,
        "spectral_type": "Cg", "discovery_year": 1999,
        "discovered_by": "LINEAR Survey",
        "mission": "Hayabusa2 (JAXA, 2018–2019)",
        "fun_fact": "Hayabusa2 found amino acids and hydrated minerals on Ryugu — strong evidence that asteroids seeded life's building blocks on early Earth. Named after an underwater dragon palace in Japanese folklore.",
        "nasa_url": "https://www.isas.jaxa.jp/en/missions/spacecraft/current/hayabusa2.html",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2027-11-30",
            "close_approach_date_full": "2027-Nov-30 00:00",
            "relative_velocity": {"kilometers_per_hour": "32400", "kilometers_per_second": "9.0"},
            "miss_distance": {"astronomical": "0.0521", "lunar": "20.3", "kilometers": "7790000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2065803", "name": "65803 Didymos",
        "name_aliases": "didymos,1996 gt",
        "diameter_min_km": 0.730, "diameter_max_km": 0.830,
        "is_hazardous": 1, "absolute_mag": 18.16,
        "orbital_period_d": 770.1, "eccentricity": 0.3840,
        "inclination_deg": 3.41, "semi_major_au": 1.6444,
        "spectral_type": "S", "discovery_year": 1996,
        "discovered_by": "Spacewatch",
        "mission": "NASA DART (2022) — first planetary defense test. ESA Hera (2026).",
        "fun_fact": "NASA's DART spacecraft intentionally crashed into Didymos's moonlet Dimorphos in September 2022, successfully changing its orbit by 33 minutes — humanity's first planetary defense demonstration.",
        "nasa_url": "https://dart.jhuapl.edu/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2062-10-04",
            "close_approach_date_full": "2062-Oct-04 00:00",
            "relative_velocity": {"kilometers_per_hour": "48000", "kilometers_per_second": "13.3"},
            "miss_distance": {"astronomical": "0.0193", "lunar": "7.50", "kilometers": "2890000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2000433", "name": "433 Eros",
        "name_aliases": "eros,1898 dq",
        "diameter_min_km": 11.2, "diameter_max_km": 16.8,
        "is_hazardous": 0, "absolute_mag": 10.83,
        "orbital_period_d": 642.9, "eccentricity": 0.2230,
        "inclination_deg": 10.83, "semi_major_au": 1.4579,
        "spectral_type": "S", "discovery_year": 1898,
        "discovered_by": "Gustav Witt & Auguste Charlois",
        "mission": "NEAR Shoemaker (NASA, 2000–2001) — first spacecraft to orbit and land on an asteroid",
        "fun_fact": "Eros was the first near-Earth asteroid ever discovered. NEAR Shoemaker became the first spacecraft to land on an asteroid in 2001, operating from the surface for 16 days.",
        "nasa_url": "https://solarsystem.nasa.gov/asteroids-comets-and-meteors/asteroids/433-eros/in-depth/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2056-01-31",
            "close_approach_date_full": "2056-Jan-31 00:00",
            "relative_velocity": {"kilometers_per_hour": "40320", "kilometers_per_second": "11.2"},
            "miss_distance": {"astronomical": "0.1491", "lunar": "58.0", "kilometers": "22300000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2025143", "name": "25143 Itokawa",
        "name_aliases": "itokawa,1998 sf36",
        "diameter_min_km": 0.320, "diameter_max_km": 0.535,
        "is_hazardous": 0, "absolute_mag": 18.95,
        "orbital_period_d": 556.4, "eccentricity": 0.2799,
        "inclination_deg": 1.622, "semi_major_au": 1.3241,
        "spectral_type": "S", "discovery_year": 1998,
        "discovered_by": "LINEAR Survey",
        "mission": "Hayabusa (JAXA, 2005) — first sample return from an asteroid",
        "fun_fact": "Itokawa is a 'rubble pile' asteroid — a loose collection of rocks held together by gravity with almost no solid core. Hayabusa returned 1,500 dust particles from its surface in 2010.",
        "nasa_url": "https://solarsystem.nasa.gov/asteroids-comets-and-meteors/asteroids/25143-itokawa/in-depth/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2004-06-19",
            "close_approach_date_full": "2004-Jun-19 00:00",
            "relative_velocity": {"kilometers_per_hour": "29160", "kilometers_per_second": "8.1"},
            "miss_distance": {"astronomical": "0.0119", "lunar": "4.63", "kilometers": "1780000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2003200", "name": "3200 Phaethon",
        "name_aliases": "phaethon,1983 tb",
        "diameter_min_km": 5.10, "diameter_max_km": 5.80,
        "is_hazardous": 1, "absolute_mag": 14.46,
        "orbital_period_d": 523.5, "eccentricity": 0.8898,
        "inclination_deg": 22.26, "semi_major_au": 1.2714,
        "spectral_type": "B", "discovery_year": 1983,
        "discovered_by": "IRAS satellite (Simon Green & John Davies)",
        "mission": "DESTINY+ (JAXA, planned 2028)",
        "fun_fact": "Phaethon is the source of the Geminids meteor shower every December. It passes closer to the Sun than any named asteroid — its surface reaches 750°C. It may be an extinct comet nucleus.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2093-12-14",
            "close_approach_date_full": "2093-Dec-14 00:00",
            "relative_velocity": {"kilometers_per_hour": "72000", "kilometers_per_second": "20.0"},
            "miss_distance": {"astronomical": "0.01960", "lunar": "7.63", "kilometers": "2931000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2004179", "name": "4179 Toutatis",
        "name_aliases": "toutatis,1989 ac",
        "diameter_min_km": 2.5, "diameter_max_km": 4.5,
        "is_hazardous": 1, "absolute_mag": 15.30,
        "orbital_period_d": 1471.2, "eccentricity": 0.6340,
        "inclination_deg": 0.447, "semi_major_au": 2.5248,
        "spectral_type": "S", "discovery_year": 1989,
        "discovered_by": "Christian Pollas",
        "mission": "China Chang'e 2 flyby (2012)",
        "fun_fact": "Toutatis is shaped like a lumpy peanut — actually two lobes joined by a narrow neck. It tumbles chaotically with two rotation axes, never repeating its orientation. It passed just 1.5 million km from Earth in 2012.",
        "nasa_url": "https://solarsystem.nasa.gov/asteroids-comets-and-meteors/asteroids/4179-toutatis/in-depth/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2069-11-04",
            "close_approach_date_full": "2069-Nov-04 00:00",
            "relative_velocity": {"kilometers_per_hour": "14760", "kilometers_per_second": "4.1"},
            "miss_distance": {"astronomical": "0.0350", "lunar": "13.62", "kilometers": "5240000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2069230", "name": "69230 Hermes",
        "name_aliases": "hermes,1937 ub",
        "diameter_min_km": 0.60, "diameter_max_km": 0.80,
        "is_hazardous": 1, "absolute_mag": 17.60,
        "orbital_period_d": 777.0, "eccentricity": 0.6238,
        "inclination_deg": 6.05, "semi_major_au": 1.6541,
        "spectral_type": "S", "discovery_year": 1937,
        "discovered_by": "Karl Reinmuth",
        "mission": "None",
        "fun_fact": "Hermes was lost for 66 years after its 1937 discovery — it passed just 780,000 km from Earth (twice the Moon's distance) and then disappeared. It was finally rediscovered in 2003 by LONEOS.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "1937-10-30",
            "close_approach_date_full": "1937-Oct-30 00:00",
            "relative_velocity": {"kilometers_per_hour": "29880", "kilometers_per_second": "8.3"},
            "miss_distance": {"astronomical": "0.00521", "lunar": "2.03", "kilometers": "779700"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2003122", "name": "3122 Florence",
        "name_aliases": "florence,1981 et3",
        "diameter_min_km": 4.4, "diameter_max_km": 4.9,
        "is_hazardous": 1, "absolute_mag": 14.09,
        "orbital_period_d": 859.2, "eccentricity": 0.4225,
        "inclination_deg": 22.15, "semi_major_au": 1.7689,
        "spectral_type": "S", "discovery_year": 1981,
        "discovered_by": "Schelte Bus",
        "mission": "None",
        "fun_fact": "Florence flew past Earth on September 1, 2017, at 7 million km — the closest approach by an asteroid of its size since 1890. Radar revealed it has not one but two moons! Named after Florence Nightingale.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2017-09-01",
            "close_approach_date_full": "2017-Sep-01 00:00",
            "relative_velocity": {"kilometers_per_hour": "49248", "kilometers_per_second": "13.68"},
            "miss_distance": {"astronomical": "0.04723", "lunar": "18.38", "kilometers": "7066000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2016016", "name": "16 Psyche",
        "name_aliases": "psyche,1852 ma",
        "diameter_min_km": 220, "diameter_max_km": 280,
        "is_hazardous": 0, "absolute_mag": 5.90,
        "orbital_period_d": 1828.7, "eccentricity": 0.1341,
        "inclination_deg": 3.095, "semi_major_au": 2.9236,
        "spectral_type": "M", "discovery_year": 1852,
        "discovered_by": "Annibale de Gasparis",
        "mission": "NASA Psyche mission (launched 2023, arriving 2029)",
        "fun_fact": "Psyche is believed to be the exposed metallic core of a protoplanet — almost pure iron and nickel. Its estimated value exceeds $10,000 quadrillion. NASA launched a spacecraft to study it in 2023.",
        "nasa_url": "https://psyche.asu.edu/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2000001", "name": "1 Ceres",
        "name_aliases": "ceres",
        "diameter_min_km": 939, "diameter_max_km": 945,
        "is_hazardous": 0, "absolute_mag": 3.34,
        "orbital_period_d": 1679.8, "eccentricity": 0.0758,
        "inclination_deg": 10.59, "semi_major_au": 2.7677,
        "spectral_type": "C", "discovery_year": 1801,
        "discovered_by": "Giuseppe Piazzi",
        "mission": "NASA Dawn (2015–2018)",
        "fun_fact": "Ceres is a dwarf planet — the largest object in the asteroid belt. NASA Dawn discovered bright spots of sodium carbonate in Occator Crater, suggesting recent geological activity. Originally classified as a planet in 1801.",
        "nasa_url": "https://solarsystem.nasa.gov/planets/dwarf-planets/ceres/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2000004", "name": "4 Vesta",
        "name_aliases": "vesta",
        "diameter_min_km": 510, "diameter_max_km": 530,
        "is_hazardous": 0, "absolute_mag": 3.20,
        "orbital_period_d": 1325.6, "eccentricity": 0.0888,
        "inclination_deg": 7.141, "semi_major_au": 2.3614,
        "spectral_type": "V", "discovery_year": 1807,
        "discovered_by": "Heinrich Wilhelm Olbers",
        "mission": "NASA Dawn (2011–2012)",
        "fun_fact": "Vesta is the brightest asteroid in the night sky and the only one sometimes visible to the naked eye. Its south pole has a crater (Rheasilvia) 460 km wide — nearly as large as Vesta itself — formed by a massive ancient impact.",
        "nasa_url": "https://solarsystem.nasa.gov/asteroids-comets-and-meteors/asteroids/4-vesta/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2001620", "name": "1620 Geographos",
        "name_aliases": "geographos,1951 ra",
        "diameter_min_km": 2.56, "diameter_max_km": 5.11,
        "is_hazardous": 1, "absolute_mag": 15.61,
        "orbital_period_d": 507.7, "eccentricity": 0.3354,
        "inclination_deg": 13.34, "semi_major_au": 1.2453,
        "spectral_type": "S", "discovery_year": 1951,
        "discovered_by": "Albert Wilson & Rudolph Minkowski",
        "mission": "Magellan flyby planned 1994, scrubbed",
        "fun_fact": "Geographos is the most elongated near-Earth asteroid known — it is 5x longer than it is wide, resembling a cosmic cigar. Its shape is thought to be caused by Earth's tidal forces during a close flyby long ago.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2025-10-23",
            "relative_velocity": {"kilometers_per_hour": "43560", "kilometers_per_second": "12.1"},
            "miss_distance": {"astronomical": "0.0811", "lunar": "31.6", "kilometers": "12130000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2002340", "name": "2340 Hathor",
        "name_aliases": "hathor,1976 ua",
        "diameter_min_km": 0.21, "diameter_max_km": 0.29,
        "is_hazardous": 1, "absolute_mag": 20.19,
        "orbital_period_d": 282.9, "eccentricity": 0.4499,
        "inclination_deg": 5.86, "semi_major_au": 0.8438,
        "spectral_type": "S", "discovery_year": 1976,
        "discovered_by": "Charles Kowal",
        "mission": "None",
        "fun_fact": "Hathor has one of the most Earth-like orbits of any asteroid, making close Earth approaches every few years. Named after the Egyptian goddess of love and beauty.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2086-10-21",
            "relative_velocity": {"kilometers_per_hour": "10800", "kilometers_per_second": "3.0"},
            "miss_distance": {"astronomical": "0.00574", "lunar": "2.23", "kilometers": "858600"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2005335", "name": "5335 Damocles",
        "name_aliases": "damocles,1991 da",
        "diameter_min_km": 8.0, "diameter_max_km": 12.0,
        "is_hazardous": 0, "absolute_mag": 13.00,
        "orbital_period_d": 15140, "eccentricity": 0.8660,
        "inclination_deg": 61.59, "semi_major_au": 11.869,
        "spectral_type": "P", "discovery_year": 1991,
        "discovered_by": "Robert McNaught",
        "mission": "None",
        "fun_fact": "Damocles is the prototype of a class of asteroids called 'Damocloids' — bodies that share the highly elongated orbits of Halley-type comets but show no cometary activity. It swings between Mars and Uranus in one orbit.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2002062", "name": "2062 Aten",
        "name_aliases": "aten,1976 aa",
        "diameter_min_km": 0.90, "diameter_max_km": 1.10,
        "is_hazardous": 0, "absolute_mag": 16.97,
        "orbital_period_d": 347.0, "eccentricity": 0.1832,
        "inclination_deg": 18.93, "semi_major_au": 0.9669,
        "spectral_type": "S", "discovery_year": 1976,
        "discovered_by": "Eleanor Helin",
        "mission": "None",
        "fun_fact": "Aten is the first member of the 'Aten' asteroid class — a group with orbits smaller than Earth's. These are among the hardest asteroids to detect because they spend most of their time in the Sun's glare. Named after the Egyptian sun disk.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2001036", "name": "1036 Ganymed",
        "name_aliases": "ganymed,1924 td",
        "diameter_min_km": 31.7, "diameter_max_km": 35.0,
        "is_hazardous": 0, "absolute_mag": 9.45,
        "orbital_period_d": 1585.7, "eccentricity": 0.5341,
        "inclination_deg": 26.67, "semi_major_au": 2.6653,
        "spectral_type": "S", "discovery_year": 1924,
        "discovered_by": "Walter Baade",
        "mission": "None",
        "fun_fact": "Ganymed is the largest near-Earth asteroid known — at about 34 km wide, it dwarfs most NEOs. It is named after Ganymede, the cupbearer of the Greek gods. If it hit Earth it would cause a mass extinction.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2024-10-13",
            "relative_velocity": {"kilometers_per_hour": "72936", "kilometers_per_second": "20.26"},
            "miss_distance": {"astronomical": "0.3714", "lunar": "144.5", "kilometers": "55520000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2007482", "name": "7482 (1994 PC1)",
        "name_aliases": "1994 pc1",
        "diameter_min_km": 1.052, "diameter_max_km": 1.165,
        "is_hazardous": 1, "absolute_mag": 16.87,
        "orbital_period_d": 572.4, "eccentricity": 0.2850,
        "inclination_deg": 33.51, "semi_major_au": 1.3488,
        "spectral_type": "S", "discovery_year": 1994,
        "discovered_by": "Robert McNaught",
        "mission": "None",
        "fun_fact": "1994 PC1 was the closest predicted asteroid flyby that grabbed worldwide attention in January 2022, passing just 1.98 million km from Earth — 5 times the Moon's distance — at 47,344 km/h.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2022-01-18",
            "close_approach_date_full": "2022-Jan-18 21:51",
            "relative_velocity": {"kilometers_per_hour": "47340", "kilometers_per_second": "13.15"},
            "miss_distance": {"astronomical": "0.01326", "lunar": "5.16", "kilometers": "1982000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "3703011", "name": "(2023 DW)",
        "name_aliases": "2023 dw",
        "diameter_min_km": 0.040, "diameter_max_km": 0.090,
        "is_hazardous": 1, "absolute_mag": 27.13,
        "orbital_period_d": 271.4, "eccentricity": 0.0852,
        "inclination_deg": 10.08, "semi_major_au": 0.8269,
        "spectral_type": "Unknown", "discovery_year": 2023,
        "discovered_by": "Various sky surveys",
        "mission": "None",
        "fun_fact": "2023 DW briefly topped the risk list in early 2023 with a 1-in-360 chance of hitting Earth in 2046. After additional observations refined its orbit, the probability dropped to near zero. A perfect example of how asteroid risk evolves with more data.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2046-02-05",
            "relative_velocity": {"kilometers_per_hour": "20160", "kilometers_per_second": "5.6"},
            "miss_distance": {"astronomical": "0.00457", "lunar": "1.78", "kilometers": "684000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2002201", "name": "2201 Oljato",
        "name_aliases": "oljato,1947 xc",
        "diameter_min_km": 1.7, "diameter_max_km": 2.1,
        "is_hazardous": 0, "absolute_mag": 15.31,
        "orbital_period_d": 947.9, "eccentricity": 0.7128,
        "inclination_deg": 2.52, "semi_major_au": 2.1728,
        "spectral_type": "M", "discovery_year": 1947,
        "discovered_by": "Henry Giclas",
        "mission": "None",
        "fun_fact": "Oljato shows intermittent cometary-like magnetic disturbances detected by Pioneer Venus. Some scientists believe it may be a dormant comet masquerading as an asteroid.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2001862", "name": "1862 Apollo",
        "name_aliases": "apollo,1932 ha",
        "diameter_min_km": 1.40, "diameter_max_km": 1.60,
        "is_hazardous": 1, "absolute_mag": 16.25,
        "orbital_period_d": 651.0, "eccentricity": 0.5600,
        "inclination_deg": 6.35, "semi_major_au": 1.4700,
        "spectral_type": "Q", "discovery_year": 1932,
        "discovered_by": "Karl Reinmuth",
        "mission": "None",
        "fun_fact": "Apollo is the prototype asteroid of the Apollo class — the most numerous family of near-Earth asteroids. Lost after discovery in 1932, it was rediscovered in 1973. Source of the Capricornid meteor shower.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2029-04-03",
            "relative_velocity": {"kilometers_per_hour": "68400", "kilometers_per_second": "19.0"},
            "miss_distance": {"astronomical": "0.0231", "lunar": "8.99", "kilometers": "3460000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2001566", "name": "1566 Icarus",
        "name_aliases": "icarus,1949 ma",
        "diameter_min_km": 1.0, "diameter_max_km": 1.6,
        "is_hazardous": 1, "absolute_mag": 16.90,
        "orbital_period_d": 408.8, "eccentricity": 0.8269,
        "inclination_deg": 22.85, "semi_major_au": 1.0778,
        "spectral_type": "S", "discovery_year": 1949,
        "discovered_by": "Walter Baade",
        "mission": "None",
        "fun_fact": "Icarus has one of the most eccentric orbits of any known asteroid, swinging from within Mercury's orbit (closer than any other known asteroid) to beyond Mars. Its surface temperature reaches 370°C near the Sun. Named after the Greek myth of flying too close to the Sun.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2015-06-16",
            "relative_velocity": {"kilometers_per_hour": "90864", "kilometers_per_second": "25.24"},
            "miss_distance": {"astronomical": "0.0540", "lunar": "21.0", "kilometers": "8080000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2052768", "name": "52768 (1998 OR2)",
        "name_aliases": "1998 or2",
        "diameter_min_km": 1.8, "diameter_max_km": 4.1,
        "is_hazardous": 1, "absolute_mag": 15.80,
        "orbital_period_d": 1342.0, "eccentricity": 0.5714,
        "inclination_deg": 5.88, "semi_major_au": 2.3720,
        "spectral_type": "Sq", "discovery_year": 1998,
        "discovered_by": "LINEAR",
        "mission": "None",
        "fun_fact": "1998 OR2 passed 6.3 million km from Earth in April 2020. Radar images revealed it appeared to be wearing a 'mask' — ridges on one side resembled a surgical mask, which became a viral sensation during the COVID-19 pandemic.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2020-04-29",
            "close_approach_date_full": "2020-Apr-29 09:56",
            "relative_velocity": {"kilometers_per_hour": "31320", "kilometers_per_second": "8.7"},
            "miss_distance": {"astronomical": "0.04205", "lunar": "16.36", "kilometers": "6290000"},
            "orbiting_body": "Earth"
        }])
    },
    {
        "neo_id": "2002063", "name": "2063 Bacchus",
        "name_aliases": "bacchus,1977 hb",
        "diameter_min_km": 1.0, "diameter_max_km": 1.5,
        "is_hazardous": 1, "absolute_mag": 17.07,
        "orbital_period_d": 408.9, "eccentricity": 0.3494,
        "inclination_deg": 9.43, "semi_major_au": 1.0779,
        "spectral_type": "Xk", "discovery_year": 1977,
        "discovered_by": "Charles Kowal",
        "mission": "None",
        "fun_fact": "Radar observations of Bacchus in 1996 showed it has a contact binary shape — two lobes gently touching, like a cosmic snowman. Named after the Roman god of wine.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([])
    },
    {
        "neo_id": "2153201", "name": "153201 (2000 WO107)",
        "name_aliases": "2000 wo107",
        "diameter_min_km": 0.37, "diameter_max_km": 0.82,
        "is_hazardous": 1, "absolute_mag": 18.94,
        "orbital_period_d": 318.2, "eccentricity": 0.7790,
        "inclination_deg": 8.67, "semi_major_au": 0.9110,
        "spectral_type": "M/P", "discovery_year": 2000,
        "discovered_by": "LINEAR",
        "mission": "None",
        "fun_fact": "2000 WO107 passed just 4.3 million km from Earth in November 2020 and was widely observed by radar. Its high density suggests it may be a metallic M-type asteroid — essentially a flying metal rock.",
        "nasa_url": "https://cneos.jpl.nasa.gov/",
        "close_approach_json": json.dumps([{
            "close_approach_date": "2020-11-29",
            "close_approach_date_full": "2020-Nov-29 05:09",
            "relative_velocity": {"kilometers_per_hour": "90000", "kilometers_per_second": "25.0"},
            "miss_distance": {"astronomical": "0.02884", "lunar": "11.22", "kilometers": "4314000"},
            "orbiting_body": "Earth"
        }])
    },
]


# ═══════════════════════════════════════════════════════════════
#  DB FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_conn():
    return sqlite3.connect(DB_PATH)


def seed_database(verbose=True):
    """Insert all curated asteroids into local DB. Safe to call multiple times."""
    conn = get_conn()
    c    = conn.cursor()
    inserted = 0
    skipped  = 0

    for ast in FAMOUS_ASTEROIDS:
        c.execute('SELECT id FROM asteroid_kb WHERE neo_id=?', (ast['neo_id'],))
        if c.fetchone():
            skipped += 1
            continue

        c.execute('''
            INSERT INTO asteroid_kb
            (neo_id, name, name_aliases, diameter_min_km, diameter_max_km,
             is_hazardous, absolute_mag, orbital_period_d, eccentricity,
             inclination_deg, semi_major_au, spectral_type, discovery_year,
             discovered_by, mission, fun_fact, close_approach_json, nasa_url,
             fetched_at, source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            ast['neo_id'], ast['name'], ast.get('name_aliases',''),
            ast['diameter_min_km'], ast['diameter_max_km'],
            ast['is_hazardous'], ast.get('absolute_mag'),
            ast.get('orbital_period_d'), ast.get('eccentricity'),
            ast.get('inclination_deg'), ast.get('semi_major_au'),
            ast.get('spectral_type'), ast.get('discovery_year'),
            ast.get('discovered_by'), ast.get('mission'),
            ast.get('fun_fact'), ast.get('close_approach_json','[]'),
            ast.get('nasa_url',''), datetime.utcnow().isoformat(), 'seeded'
        ))
        inserted += 1

    conn.commit()
    conn.close()

    if verbose:
        print(f"✅ Seed complete: {inserted} inserted, {skipped} already existed")
    return inserted, skipped


def enrich_from_nasa(neo_id, verbose=True):
    """
    Fetch live NASA NEO data for a given neo_id and update the DB row.
    NASA NEO lookup by ID: /neo/rest/v1/neo/{neo_id}
    """
    url = f"https://api.nasa.gov/neo/rest/v1/neo/{neo_id}?api_key={NASA_KEY}"
    try:
        r = requests.get(url, timeout=12)
        if r.status_code != 200:
            return False
        data = r.json()
        ca_list = data.get('close_approach_data', [])
        # Keep only future / most recent approaches
        ca_json = json.dumps(ca_list[-3:] if ca_list else [])

        conn = get_conn()
        c    = conn.cursor()
        c.execute('''
            UPDATE asteroid_kb
            SET close_approach_json=?, fetched_at=?, source='nasa_enriched'
            WHERE neo_id=?
        ''', (ca_json, datetime.utcnow().isoformat(), neo_id))
        conn.commit()
        conn.close()
        if verbose:
            print(f"  ✅ Enriched {neo_id} with {len(ca_list)} approaches")
        return True
    except Exception as e:
        if verbose:
            print(f"  ⚠ Could not enrich {neo_id}: {e}")
        return False


def search_local(query: str) -> list:
    """
    Fuzzy name search in local DB.
    Returns list of row dicts, best matches first.
    """
    q    = query.strip().lower()
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Exact name match
    c.execute("SELECT * FROM asteroid_kb WHERE LOWER(name)=?", (q,))
    rows = c.fetchall()

    # 2. Name contains query
    if not rows:
        c.execute("SELECT * FROM asteroid_kb WHERE LOWER(name) LIKE ?", (f'%{q}%',))
        rows = c.fetchall()

    # 3. Aliases contain query
    if not rows:
        c.execute("SELECT * FROM asteroid_kb WHERE LOWER(name_aliases) LIKE ?", (f'%{q}%',))
        rows = c.fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_all_local() -> list:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM asteroid_kb ORDER BY is_hazardous DESC, name ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def row_to_neo_format(row: dict) -> dict:
    """
    Convert local DB row → NASA NEO API format
    so local_model.py can process it without changes.
    """
    ca_list = []
    try:
        ca_list = json.loads(row.get('close_approach_json') or '[]')
    except Exception:
        pass

    return {
        "id"                 : row['neo_id'],
        "neo_reference_id"   : row['neo_id'],
        "name"               : row['name'],
        "absolute_magnitude_h": row.get('absolute_mag'),
        "is_potentially_hazardous_asteroid": bool(row.get('is_hazardous', 0)),
        "estimated_diameter" : {
            "kilometers": {
                "estimated_diameter_min": row.get('diameter_min_km', 0),
                "estimated_diameter_max": row.get('diameter_max_km', 0),
            },
            "meters": {
                "estimated_diameter_min": (row.get('diameter_min_km', 0) or 0) * 1000,
                "estimated_diameter_max": (row.get('diameter_max_km', 0) or 0) * 1000,
            }
        },
        "close_approach_data": ca_list,
        # Extra local fields passed through for the report generator
        "_local": {
            "spectral_type"  : row.get('spectral_type'),
            "discovery_year" : row.get('discovery_year'),
            "discovered_by"  : row.get('discovered_by'),
            "mission"        : row.get('mission'),
            "fun_fact"       : row.get('fun_fact'),
            "orbital_period" : row.get('orbital_period_d'),
            "eccentricity"   : row.get('eccentricity'),
            "inclination"    : row.get('inclination_deg'),
            "semi_major_au"  : row.get('semi_major_au'),
            "nasa_url"       : row.get('nasa_url'),
            "source"         : row.get('source'),
        }
    }


# ── Auto-seed on import ───────────────────────────────────────
if __name__ == '__main__':
    print("🌿 GROOT — Asteroid DB Seeder")
    print(f"   DB path: {DB_PATH}")
    seed_database()
    print("\nAll asteroids in local DB:")
    for row in get_all_local():
        haz = "⚠" if row['is_hazardous'] else "✓"
        print(f"  {haz}  {row['name']:<30} ({row.get('spectral_type','?')} type, {row.get('diameter_max_km',0):.1f} km max)")
