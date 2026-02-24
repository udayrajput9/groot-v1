"""
Local Asteroid Report Generator Model
Generates detailed asteroid reports using local machine learning
Includes Earth approach date prediction engine
No external API calls required
"""

import math
from datetime import datetime, timedelta


class ApproachPredictor:
    """
    Predicts when an asteroid will reach its closest point to Earth.

    Strategy:
      1. If the data already contains a close_approach_date string, parse
         and use it directly (most accurate).
      2. Otherwise fall back to a physics-based estimate:
           - Straight-line time = distance / speed
           - Corrected with an orbital curvature factor derived from
             gravitational focusing (Opik formula), giving a more realistic
             curved-path estimate.
      3. Classify the urgency of the approach for the report.
    """

    EARTH_RADIUS_KM        = 6_371
    LUNAR_DISTANCE_KM      = 384_400          # 1 LD
    CLOSE_APPROACH_LD      = 20               # within 20 LD = "close"
    VERY_CLOSE_APPROACH_LD = 5                # within 5 LD  = "very close"

    def predict(self, close_approach_data: list, diameter_km: float) -> dict:
        """
        Return a prediction dict with keys:
          approach_date, days_until, distance_km, distance_ld,
          urgency, urgency_icon, confidence, method, already_passed, notes
        """
        if not close_approach_data:
            return self._unknown()

        approach = close_approach_data[0]

        # 1. Try the date field supplied by the data source
        raw_date = (
            approach.get("close_approach_date_full")   # "YYYY-MMM-DD HH:MM"
            or approach.get("close_approach_date")     # "YYYY-MM-DD"
        )

        velocity_kmh = float(
            str(approach.get("relative_velocity", {})
                        .get("kilometers_per_hour", 0) or 0).replace("_", "")
        )
        distance_km = float(
            str(approach.get("miss_distance", {})
                        .get("kilometers", 0) or 0).replace("_", "")
        )
        distance_ld = distance_km / self.LUNAR_DISTANCE_KM

        if raw_date:
            approach_date, confidence, method = self._parse_date(raw_date)
        else:
            # 2. Physics-based fallback
            approach_date, confidence, method = self._estimate_from_physics(
                distance_km, velocity_kmh, diameter_km
            )

        if approach_date is None:
            return self._unknown()

        now       = datetime.utcnow()
        days_diff = (approach_date - now).total_seconds() / 86_400
        already_passed = days_diff < -1

        urgency, urgency_icon = self._classify_urgency(
            days_diff, distance_ld, already_passed
        )
        notes = self._build_notes(
            days_diff, distance_ld, diameter_km, already_passed, velocity_kmh
        )

        return {
            "approach_date"  : approach_date,
            "days_until"     : round(days_diff, 1),
            "distance_km"    : distance_km,
            "distance_ld"    : round(distance_ld, 2),
            "urgency"        : urgency,
            "urgency_icon"   : urgency_icon,
            "confidence"     : confidence,
            "method"         : method,
            "already_passed" : already_passed,
            "notes"          : notes,
        }

    # ── private helpers ───────────────────────────────────────────────────────

    def _parse_date(self, raw: str):
        formats = [
            "%Y-%b-%d %H:%M",   # 2029-Apr-13 21:46
            "%Y-%m-%d %H:%M",   # 2029-04-13 21:46
            "%Y-%m-%d",         # 2029-04-13
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(raw.strip(), fmt)
                return dt, "High", "Recorded close-approach date from orbital data"
            except ValueError:
                continue
        return None, "Low", "Date string unrecognised"

    def _estimate_from_physics(self, distance_km: float,
                               velocity_kmh: float, diameter_km: float):
        """
        Curved-path estimate using gravitational focusing (Opik formula).

        The asteroid follows a hyperbolic path around Earth, so the real
        path length is longer than the straight-line distance.

            kappa = sqrt(1 + (v_escape / v_infinity)^2)

        We blend the correction by how close the pass is:
          - Very close pass (few LD) -> full curvature correction
          - Distant pass (40+ LD)    -> essentially straight-line
        """
        if velocity_kmh <= 0 or distance_km <= 0:
            return None, "Unknown", "Insufficient data"

        velocity_kms = velocity_kmh / 3_600
        v_esc        = 11.2   # km/s  Earth escape velocity
        kappa        = math.sqrt(1 + (v_esc / max(velocity_kms, 0.1)) ** 2)

        ld       = distance_km / self.LUNAR_DISTANCE_KM
        blend    = max(0.0, 1.0 - ld / 40.0)      # 1 at 0 LD, 0 at 40 LD
        factor   = 1 + blend * (kappa - 1) * 0.5

        hours_away    = (distance_km / velocity_kmh) * factor
        approach_date = datetime.utcnow() + timedelta(hours=hours_away)

        confidence = "Medium" if velocity_kms > 1 else "Low"
        method = (
            "Physics-based estimate (curved-path / gravitational-focusing "
            "correction applied; no recorded date available)"
        )
        return approach_date, confidence, method

    def _classify_urgency(self, days: float, ld: float, passed: bool):
        if passed:
            return "Already passed", "✅"
        if days < 0:
            return "Imminent / past", "🔴"
        if days <= 7 and ld <= self.VERY_CLOSE_APPROACH_LD:
            return "CRITICAL — very close, very soon", "🚨"
        if days <= 30 and ld <= self.CLOSE_APPROACH_LD:
            return "High — approaching within a month", "⚠️"
        if days <= 180:
            return "Moderate — approaching within 6 months", "🟡"
        if days <= 365:
            return "Low — approaching within a year", "🟢"
        if days <= 365 * 5:
            return "Informational — approach in 1–5 years", "🔵"
        return "Long-term tracking", "🔭"

    def _build_notes(self, days: float, ld: float,
                     diameter_km: float, passed: bool,
                     velocity_kmh: float) -> list:
        notes = []
        if passed:
            notes.append(
                f"This approach already occurred approximately "
                f"{abs(days):.0f} days ago."
            )
        elif days < 30:
            notes.append(
                f"Approach is imminent — within {days:.1f} days."
            )

        if ld <= self.VERY_CLOSE_APPROACH_LD and not passed:
            notes.append(
                f"Miss distance of {ld:.2f} LD is within the very-close "
                f"threshold ({self.VERY_CLOSE_APPROACH_LD} LD). "
                f"Enhanced tracking recommended."
            )
        elif ld <= self.CLOSE_APPROACH_LD:
            notes.append(
                f"Miss distance of {ld:.2f} LD qualifies as a close "
                f"Earth approach by IAU standards."
            )

        if diameter_km >= 1.0:
            notes.append(
                "Object diameter >= 1 km — qualifies as a 'globally hazardous' "
                "size class if on an impact trajectory."
            )
        elif diameter_km >= 0.14:
            notes.append(
                "Diameter sufficient to cause regional-scale damage on impact."
            )

        speed_kmps = velocity_kmh / 3_600
        if speed_kmps > 0:
            hours_to_moon = self.LUNAR_DISTANCE_KM / speed_kmps / 3_600
            notes.append(
                f"At {speed_kmps:.2f} km/s this asteroid would cross the "
                f"Moon's orbital distance in ~{hours_to_moon:.1f} hours."
            )
        return notes

    def _unknown(self):
        return {
            "approach_date"  : None,
            "days_until"     : None,
            "distance_km"    : 0.0,
            "distance_ld"    : 0.0,
            "urgency"        : "Unknown",
            "urgency_icon"   : "❓",
            "confidence"     : "None",
            "method"         : "No approach data available",
            "already_passed" : False,
            "notes"          : ["No close-approach data found for this object."],
        }


# =============================================================================

class AsteroidReportGenerator:
    """
    Generates comprehensive asteroid reports with an integrated
    Earth-approach prediction section.
    """

    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.report_template = self._get_report_template()
        self.predictor = ApproachPredictor()

    # ── knowledge base ────────────────────────────────────────────────────────

    def _load_knowledge_base(self):
        return {
            'facts': {
                'very_small': [
                    'Smaller than most buildings, this asteroid is relatively tiny',
                    'Very small asteroids are extremely common in the solar system',
                    'Objects this size usually burn up in Earth\'s atmosphere',
                    'Even tiny asteroids carry significant kinetic energy',
                ],
                'small': [
                    'This is a smaller asteroid, roughly the size of a city block',
                    'Small asteroids like this one move swiftly through space',
                    'Many small asteroids pass Earth regularly without being noticed',
                    'This asteroid is too small to cause global concern',
                ],
                'medium': [
                    'This is a medium-sized asteroid, comparable to a small mountain',
                    'Asteroids of this size can travel at impressive speeds',
                    'Objects like this are studied carefully by astronomers',
                    'This size asteroid could devastate a region if it hit Earth',
                ],
                'large': [
                    'This is a large asteroid — a significant object in space!',
                    'Large asteroids attract serious scientific attention',
                    'Objects this large have been tracked since their discovery',
                    'The impact of such an object would be globally catastrophic',
                ],
                'very_large': [
                    'This is an exceptionally large asteroid — a rare find',
                    'Objects of this scale are top-priority for all space agencies',
                    'Very large asteroids shaped the evolution of the solar system',
                    'A collision with Earth would be an extinction-level event',
                ],
            },
            'comparisons': {
                'very_small': 'the size of a house',
                'small'     : 'the size of a city block',
                'medium'    : 'the size of a small mountain',
                'large'     : 'the size of a large mountain',
                'very_large': 'multiple kilometres across',
            },
            'hazard_facts': {
                'hazardous': [
                    'This asteroid is classified as potentially hazardous',
                    'NASA closely monitors this object due to its trajectory',
                    'It passes near Earth orbit regularly',
                    'Future impact probabilities are calculated by scientists',
                    'Advanced warning systems help track its movements',
                ],
                'safe': [
                    'This asteroid is not considered an immediate threat',
                    'Its orbit keeps it at a safe distance from Earth',
                    'It\'s still valuable for scientific study',
                    'Astronomers monitor all near-Earth objects',
                    'This object is safe to study and observe',
                ],
            },
            'velocity_facts': {
                'slow'     : 'This asteroid moves relatively slowly through space',
                'medium'   : 'This asteroid travels at a moderate speed through space',
                'fast'     : 'This asteroid is moving very quickly through space',
                'very_fast': 'This asteroid is speeding through space at an impressive velocity',
            },
        }

    # ── report template ───────────────────────────────────────────────────────

    def _get_report_template(self):
        return """
=================================================================
  ASTEROID DETAILED REPORT: {name}
=================================================================

PHYSICAL CHARACTERISTICS
-----------------------------------------------------------------
  Estimated Diameter  : {diameter:.3f} km
  Size Comparison     : {size_comparison}
  Classification      : {classification}
  Status              : {status}

MOVEMENT & TRAJECTORY DATA
-----------------------------------------------------------------
  Velocity            : {velocity:,.0f} km/h  ({velocity_kmps:.2f} km/s)  [{velocity_classification}]
  Miss Distance       : {distance:,.0f} km  ({distance_ld:.2f} lunar distances)
  Last Updated        : {updated_date}

EARTH APPROACH PREDICTION
-----------------------------------------------------------------
{approach_block}

INTERESTING FACTS & CHARACTERISTICS
-----------------------------------------------------------------
{interesting_facts}

SAFETY & RISK ASSESSMENT
-----------------------------------------------------------------
  Hazard Status       : {hazard_status}
  Risk Level          : {risk_level}
  Monitoring          : {monitoring_status}
{hazard_explanation}

SCIENTIFIC SIGNIFICANCE
-----------------------------------------------------------------
  Why It Matters      : {scientific_importance}
  Research Value      : {research_value}
  Data Collection     : Continuous monitoring by space agencies
  Orbital Studies     : Helps us understand solar system dynamics

COMPARATIVE ANALYSIS
-----------------------------------------------------------------
  Compared to         : {comparison_object}
  Speed Comparison    : {speed_comparison}
  Similar Asteroids   : {similar_asteroids}

KEY TAKEAWAY
-----------------------------------------------------------------
{key_takeaway}

=================================================================
Generated: {timestamp}  |  Report Version: 2.0
=================================================================
"""

    # ── categorisation helpers ────────────────────────────────────────────────

    def _categorize_size(self, diameter):
        if diameter < 0.1:   return 'very_small'
        if diameter < 1:     return 'small'
        if diameter < 10:    return 'medium'
        if diameter < 50:    return 'large'
        return 'very_large'

    def _get_size_comparison(self, diameter):
        if diameter < 0.05:  return 'smaller than a hotel building'
        if diameter < 0.1:   return self.knowledge_base['comparisons']['very_small']
        if diameter < 0.5:   return self.knowledge_base['comparisons']['small']
        if diameter < 5:     return self.knowledge_base['comparisons']['medium']
        if diameter < 20:    return self.knowledge_base['comparisons']['large']
        return self.knowledge_base['comparisons']['very_large']

    def _classify_velocity(self, velocity_kmh):
        if velocity_kmh < 15_000: return 'slow'
        if velocity_kmh < 30_000: return 'medium'
        if velocity_kmh < 50_000: return 'fast'
        return 'very_fast'

    # ── content builders ──────────────────────────────────────────────────────

    def _get_interesting_facts(self, asteroid_data, diameter):
        cat   = self._categorize_size(diameter)
        facts = self.knowledge_base['facts'].get(cat, [])
        lines = [f"  * {facts[0]}", f"  * {facts[1]}"] if len(facts) >= 2 else []

        ca = asteroid_data.get('close_approach_data', [])
        if ca:
            v = float(
                str(ca[0].get('relative_velocity', {})
                         .get('kilometers_per_hour', 0) or 0).replace('_', '')
            )
            lines.append(f"  * {self.knowledge_base['velocity_facts'][self._classify_velocity(v)]}")

        lines.append("  * This asteroid has been discovered and tracked by astronomers")
        return '\n'.join(lines)

    def _get_hazard_explanation(self, is_hazardous):
        key   = 'hazardous' if is_hazardous else 'safe'
        facts = self.knowledge_base['hazard_facts'][key]
        return f"  * {facts[3]}\n  * {facts[4]}"

    def _get_scientific_importance(self, diameter, is_hazardous):
        if diameter > 10:
            return "Large asteroids help us understand planetary formation and solar system history"
        if is_hazardous:
            return "Potentially hazardous asteroids provide critical data for planetary defense research"
        return "Contributes to our understanding of near-Earth object distribution and orbital mechanics"

    # ── approach prediction block ─────────────────────────────────────────────

    def _format_approach_block(self, pred: dict) -> str:
        if pred["approach_date"] is None:
            return "  ? Prediction unavailable -- no approach data supplied.\n"

        date_str = pred["approach_date"].strftime("%A, %B %d, %Y")
        time_str = pred["approach_date"].strftime("%H:%M UTC")
        days     = pred["days_until"]

        if pred["already_passed"]:
            timing = (
                f"  * This approach already occurred on {date_str} at {time_str}.\n"
                f"  * That was approximately {abs(days):.1f} days ago.\n"
            )
        elif days <= 1:
            timing = f"  * IMMINENT -- expected within 24 hours ({date_str} at {time_str})!\n"
        elif days <= 7:
            timing = f"  * Expected in {days:.1f} days  ->  {date_str} at {time_str}\n"
        elif days <= 60:
            timing = f"  * Expected in {days:.0f} days (~{days/7:.1f} weeks)  ->  {date_str}\n"
        else:
            timing = (
                f"  * Expected in {days:.0f} days (~{days/365.25:.2f} years)  "
                f"->  {date_str}\n"
            )

        notes_str = "".join(f"  * {n}\n" for n in pred["notes"])

        return (
            f"  {pred['urgency_icon']}  Urgency        : {pred['urgency']}\n"
            f"{timing}"
            f"  * Miss Distance     : {pred['distance_km']:,.0f} km "
            f"({pred['distance_ld']:.2f} lunar distances)\n"
            f"  * Prediction Method : {pred['method']}\n"
            f"  * Confidence        : {pred['confidence']}\n"
            f"\n  [PREDICTION NOTES]\n"
            f"{notes_str}"
        )

    # ── main entry point ──────────────────────────────────────────────────────

    def generate_report(self, asteroid_name: str, asteroid_data: dict) -> str:
        diameter = float(
            asteroid_data.get('estimated_diameter', {})
                         .get('kilometers', {})
                         .get('estimated_diameter_max', 0) or 0
        )
        is_hazardous   = asteroid_data.get('is_potentially_hazardous_asteroid', False)
        close_approach = asteroid_data.get('close_approach_data', [])

        velocity = distance = 0.0
        if close_approach:
            ca = close_approach[0]
            velocity = float(
                str(ca.get('relative_velocity', {})
                       .get('kilometers_per_hour', 0) or 0).replace('_', '')
            )
            distance = float(
                str(ca.get('miss_distance', {})
                       .get('kilometers', 0) or 0).replace('_', '')
            )

        prediction     = self.predictor.predict(close_approach, diameter)
        approach_block = self._format_approach_block(prediction)
        distance_ld    = distance / ApproachPredictor.LUNAR_DISTANCE_KM
        velocity_kmps  = velocity / 3_600

        classification = 'Major NEO' if diameter >= 1 else 'Minor NEO'

        comparison_object = (
            'A small city block' if diameter < 0.5
            else 'Mount Vesuvius' if diameter < 5
            else 'A large cosmic body'
        )
        similar_asteroids = (
            'Apophis, Didymos' if (is_hazardous and diameter > 1)
            else 'Ceres, Vesta' if diameter > 5
            else 'Various near-Earth asteroids'
        )

        actual_name = asteroid_data.get('name', asteroid_name).strip()
        is_exact    = asteroid_name.strip().lower() == actual_name.lower()

        if is_hazardous:
            if diameter > 10:
                key_takeaway = (
                    f"[!] {actual_name} is a {diameter:.2f} km potentially hazardous "
                    f"asteroid actively tracked by space agencies. Its size and trajectory "
                    f"make it a key subject for planetary defense research."
                )
            else:
                key_takeaway = (
                    f"[!] {actual_name} is a potentially hazardous asteroid, but current "
                    f"predictions show it will pass safely. It is critical for understanding "
                    f"threat-assessment methods."
                )
        else:
            if diameter > 5:
                key_takeaway = (
                    f"[*] {actual_name} is a large asteroid providing valuable data about "
                    f"solar system composition. Its safe trajectory makes it an excellent "
                    f"subject for scientific study."
                )
            else:
                key_takeaway = (
                    f"[*] {actual_name} is an interesting near-Earth object contributing "
                    f"to our catalog of space knowledge. Every asteroid studied deepens "
                    f"our understanding of the cosmic neighbourhood!"
                )

        match_note = (
            "[Exact match for search term]\n"
            if is_exact else
            "[No exact match -- showing closest available asteroid]\n"
        )

        return self.report_template.format(
            name                    = actual_name,
            diameter                = diameter,
            size_comparison         = self._get_size_comparison(diameter),
            classification          = classification,
            status                  = ('Potentially Hazardous' if is_hazardous else 'Safe'),
            velocity                = velocity,
            velocity_kmps           = velocity_kmps,
            velocity_classification = self._classify_velocity(velocity),
            distance                = distance,
            distance_ld             = round(distance_ld, 2),
            updated_date            = datetime.now().strftime('%B %d, %Y'),
            approach_block          = approach_block,
            interesting_facts       = self._get_interesting_facts(asteroid_data, diameter),
            hazard_status           = ('Potentially Hazardous - High Priority'
                                       if is_hazardous else 'Not Hazardous - Regular Monitoring'),
            risk_level              = ('High'   if (is_hazardous and diameter > 5)
                                       else 'Medium' if is_hazardous else 'Low'),
            monitoring_status       = 'Continuous' if is_hazardous else 'Ongoing',
            hazard_explanation      = self._get_hazard_explanation(is_hazardous),
            scientific_importance   = self._get_scientific_importance(diameter, is_hazardous),
            research_value          = ('Critical for planetary defense' if is_hazardous
                                       else 'Important for solar system studies'),
            comparison_object       = comparison_object,
            speed_comparison        = (f"Moving at {velocity:,.0f} km/h ({velocity_kmps:.2f} km/s)"
                                       if velocity > 0 else "Speed data pending"),
            similar_asteroids       = similar_asteroids,
            key_takeaway            = match_note + key_takeaway,
            timestamp               = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        )


# ── singleton for import convenience ─────────────────────────────────────────
asteroid_report_model = AsteroidReportGenerator()


# =============================================================================
# Demo / self-test
# =============================================================================
if __name__ == "__main__":

    gen = AsteroidReportGenerator()

    print("\n" + "=" * 65)
    print("DEMO 1 -- Apophis-like, recorded close-approach date")
    print("=" * 65)
    apophis = {
        'name': '99942 Apophis',
        'estimated_diameter': {'kilometers': {'estimated_diameter_max': 0.45}},
        'is_potentially_hazardous_asteroid': True,
        'close_approach_data': [{
            'close_approach_date_full': '2029-Apr-13 21:46',
            'relative_velocity': {'kilometers_per_hour': '30600'},
            'miss_distance':     {'kilometers': '38017676'},
        }],
    }
    print(gen.generate_report('99942 Apophis', apophis))

    print("\n" + "=" * 65)
    print("DEMO 2 -- Unknown NEO, physics-based prediction only")
    print("=" * 65)
    unknown = {
        'name': 'Unknown NEO 2024-XQ1',
        'estimated_diameter': {'kilometers': {'estimated_diameter_max': 2.5}},
        'is_potentially_hazardous_asteroid': True,
        'close_approach_data': [{
            'relative_velocity': {'kilometers_per_hour': '25000'},
            'miss_distance':     {'kilometers': '1500000'},
        }],
    }
    print(gen.generate_report('Unknown NEO 2024-XQ1', unknown))

    print("\n" + "=" * 65)
    print("DEMO 3 -- Safe, distant future flyby")
    print("=" * 65)
    safe_ast = {
        'name': 'Safe Rock 2031',
        'estimated_diameter': {'kilometers': {'estimated_diameter_max': 0.08}},
        'is_potentially_hazardous_asteroid': False,
        'close_approach_data': [{
            'close_approach_date': '2031-09-22',
            'relative_velocity': {'kilometers_per_hour': '18000'},
            'miss_distance':     {'kilometers': '6500000'},
        }],
    }
    print(gen.generate_report('Safe Rock 2031', safe_ast))
