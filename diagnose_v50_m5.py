from v50_data import get_candles
from v50_smc import (
    detect_structure,
    detect_premium_discount,
    detect_liquidity_sweep,
    find_swing_highs,
    find_swing_lows,
    classify_swings,
)

COUNT = 1000
STEP = 5
MIN_M5 = 200

print("🔬 DIAGNOSTIC CIBLÉ — CONFIRMATION M5")
print("=" * 70)
print("⚠️ Données historiques réelles Deriv.")
print("⚠️ Aucun trade réel.")
print("⚠️ Aucune modification du moteur.")
print()

h1 = get_candles("H1", COUNT)
m15 = get_candles("M15", COUNT)
m5 = get_candles("M5", COUNT)

print(f"✅ H1  : {len(h1)} bougies")
print(f"✅ M15 : {len(m15)} bougies")
print(f"✅ M5  : {len(m5)} bougies")
print()


def candles_before(candles, timestamp):
    return [c for c in candles if c["timestamp"] < timestamp]


def show_m5_details(m5_data, direction):
    structure = detect_structure(m5_data)
    sweep = detect_liquidity_sweep(m5_data)

    highs = find_swing_highs(m5_data)
    lows = find_swing_lows(m5_data)

    classified_highs, classified_lows = classify_swings(highs, lows)

    last = m5_data[-1]

    print(f"Direction recherchée : {direction}")
    print(f"Prix actuel          : {last['close']}")
    print(f"Tendance M5          : {structure['trend']}")
    print(f"BOS                  : {structure['bos']}")
    print(f"CHOCH                : {structure['choch']}")
    print(f"Niveau cassé         : {structure['broken_level']}")
    print(f"Liquidity sweep      : {sweep}")

    print(
        "Sommets M5           : "
        + " → ".join(x["label"] for x in classified_highs[-6:])
    )

    print(
        "Creux M5             : "
        + " → ".join(x["label"] for x in classified_lows[-6:])
    )

    print()
    print("Derniers swings M5 :")

    for x in highs[-3:]:
        print(
            f"  HIGH {x['timestamp']} : "
            f"{x['price']}"
        )

    for x in lows[-3:]:
        print(
            f"  LOW  {x['timestamp']} : "
            f"{x['price']}"
        )


candidates = []

for i in range(MIN_M5, len(m5) - 1, STEP):

    current = m5[i]
    timestamp = current["timestamp"]

    h1_data = candles_before(h1, timestamp)
    m15_data = candles_before(m15, timestamp)
    m5_data = m5[:i + 1]

    if len(h1_data) < 50 or len(m15_data) < 100:
        continue

    h1_structure = detect_structure(h1_data)
    m15_structure = detect_structure(m15_data)

    h1_trend = h1_structure["trend"]
    m15_trend = m15_structure["trend"]

    zone = detect_premium_discount(m15_data)

    # Configuration BUY complète jusqu'à la zone.
    if (
        h1_trend == "HAUSSIER"
        and m15_trend == "HAUSSIER"
        and zone["zone"] == "DISCOUNT"
    ):
        candidates.append(("BUY", current, h1_data, m15_data, m5_data))

    # Configuration SELL complète jusqu'à la zone.
    elif (
        h1_trend == "BAISSIER"
        and m15_trend == "BAISSIER"
        and zone["zone"] == "PREMIUM"
    ):
        candidates.append(("SELL", current, h1_data, m15_data, m5_data))


print("=" * 70)
print(f"🎯 CONFIGURATIONS TROUVÉES : {len(candidates)}")
print("=" * 70)

if not candidates:
    print("Aucune configuration H1 + M15 + zone trouvée.")
else:

    for number, (direction, current, h1_data, m15_data, m5_data) in enumerate(
        candidates, 1
    ):

        print()
        print("=" * 70)
        print(f"📌 CONFIGURATION #{number}")
        print("=" * 70)

        print(f"Date/heure : {current['datetime']}")
        print(f"Direction  : {direction}")

        h1 = detect_structure(h1_data)
        m15 = detect_structure(m15_data)
        zone = detect_premium_discount(m15_data)

        print()
        print("H1")
        print(f"  Tendance : {h1['trend']}")
        print(f"  BOS      : {h1['bos']}")
        print(f"  CHOCH    : {h1['choch']}")

        print()
        print("M15")
        print(f"  Tendance : {m15['trend']}")
        print(f"  BOS      : {m15['bos']}")
        print(f"  CHOCH    : {m15['choch']}")
        print(f"  Zone     : {zone['zone']}")

        print()
        print("M5 — DÉTAIL")
        show_m5_details(m5_data, direction)

print()
print("=" * 70)
print("🎯 DIAGNOSTIC CIBLÉ TERMINÉ")
print("=" * 70)
