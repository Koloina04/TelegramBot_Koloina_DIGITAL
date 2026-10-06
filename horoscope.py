import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from gemini_api import generate_text

DB = "bot.db"

SIGNS = [
    "Bélier", "Taureau", "Gémeaux", "Cancer",
    "Lion", "Vierge", "Balance", "Scorpion",
    "Sagittaire", "Capricorne", "Verseau", "Poissons"
]


def init_horoscope_db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_horoscopes (
            date TEXT NOT NULL,
            sign TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, sign)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS horoscope_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            sign TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_previous_horoscopes(sign, limit=7):
    conn = sqlite3.connect(DB)

    rows = conn.execute("""
        SELECT message
        FROM horoscope_history
        WHERE sign = ?
        ORDER BY id DESC
        LIMIT ?
    """, (sign, limit)).fetchall()

    conn.close()

    return [row[0] for row in rows]


def generate_ai_horoscope(sign, date_str):
    previous = get_previous_horoscopes(sign)

    if previous:
        previous_text = "\n\n".join(
            f"- {message}" for message in previous
        )
    else:
        previous_text = "Aucun horoscope précédent."

    prompt = f"""
Tu es un rédacteur professionnel d'horoscopes en français.

Génère l'horoscope du jour pour le signe astrologique : {sign}.
Date : {date_str}

OBJECTIF :
Créer un horoscope naturel, agréable, personnalisé et différent des jours précédents.

RÈGLES :
- Ne présente pas l'astrologie comme une science ou une certitude.
- Ne prétends pas connaître exactement les événements futurs.
- Évite les prédictions catastrophiques ou alarmistes.
- Évite les répétitions de formulations et de thèmes.
- Ne mentionne jamais que tu es une IA.
- Ne parle pas des anciens horoscopes dans ta réponse.
- Réponds uniquement en français.

STRUCTURE :
🔮 Horoscope du jour — {sign}

❤️ Amour
💼 Travail & finances
🧠 État d'esprit
🍀 Conseil du jour

Chaque partie doit être concise mais intéressante.
Termine par une phrase positive.

ANCIENS HOROSCOPES À ÉVITER :
{previous_text}
"""

    return generate_text(prompt).strip()


def get_horoscope(sign):
    init_horoscope_db()

    today = datetime.now(ZoneInfo("Indian/Antananarivo")).strftime("%d/%m/%Y")

    conn = sqlite3.connect(DB)

    row = conn.execute("""
        SELECT message
        FROM daily_horoscopes
        WHERE date = ? AND sign = ?
    """, (today, sign)).fetchone()

    conn.close()

    if row:
        return row[0]

    message = generate_ai_horoscope(sign, today)

    conn = sqlite3.connect(DB)

    conn.execute("""
        INSERT OR REPLACE INTO daily_horoscopes
        (date, sign, message)
        VALUES (?, ?, ?)
    """, (today, sign, message))

    conn.execute("""
        INSERT INTO horoscope_history
        (date, sign, message)
        VALUES (?, ?, ?)
    """, (today, sign, message))

    conn.commit()
    conn.close()

    return message


def generate_all_today():
    init_horoscope_db()

    results = {}

    for sign in SIGNS:
        try:
            results[sign] = get_horoscope(sign)
        except Exception as e:
            results[sign] = f"Erreur pour {sign} : {e}"

    return results


if __name__ == "__main__":
    print("🔮 Test horoscope IA")
    print()
    print(get_horoscope("Bélier"))
