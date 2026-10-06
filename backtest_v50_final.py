from v50_data import get_candles
from v50_smc import build_signal, detect_structure, detect_premium_discount

COUNT = 1000
MAX_SETUP_AGE = 48
LOOKAHEAD = 60

print("📊 BACKTEST FINAL — SMC V50")
print("=" * 70)
print("⚠️ Données historiques réelles Deriv")
print("⚠️ Aucun trade réel")
print("⚠️ Entrée uniquement au moment de la confirmation M5")
print()

h1 = get_candles("H1", COUNT)
m15 = get_candles("M15", COUNT)
m5 = get_candles("M5", COUNT)

print(f"✅ H1  : {len(h1)}")
print(f"✅ M15 : {len(m15)}")
print(f"✅ M5  : {len(m5)}")
print()


def candles_before(candles, timestamp):
    return [c for c in candles if c["timestamp"] <= timestamp]


results = []
setups = 0
used_confirmation_timestamps = set()

for i in range(200, len(m5) - LOOKAHEAD):

    current = m5[i]
    timestamp = current["timestamp"]

    h1_data = candles_before(h1, timestamp)
    m15_data = candles_before(m15, timestamp)

    if len(h1_data) < 50 or len(m15_data) < 100:
        continue

    h1_structure = detect_structure(h1_data)
    m15_structure = detect_structure(m15_data)
    zone = detect_premium_discount(m15_data)

    direction = None

    if (
        h1_structure["trend"] == "HAUSSIER"
        and m15_structure["trend"] == "HAUSSIER"
        and zone["zone"] == "DISCOUNT"
    ):
        direction = "BUY"

    elif (
        h1_structure["trend"] == "BAISSIER"
        and m15_structure["trend"] == "BAISSIER"
        and zone["zone"] == "PREMIUM"
    ):
        direction = "SELL"

    if direction is None:
        continue

    setups += 1

    # --------------------------------------------------------
    # Recherche de confirmation M5 pendant maximum 48 bougies
    # --------------------------------------------------------

    signal = None
    confirmation_index = None

    for step in range(0, MAX_SETUP_AGE + 1):

        j = i + step

        if j >= len(m5):
            break

        m5_data = m5[:j + 1]

        candidate = build_signal(
            h1_data,
            m15_data,
            m5_data,
        )

        if candidate and candidate["direction"] == direction:
            signal = candidate
            confirmation_index = j
            break

    if signal is None:
        continue

    confirmation_timestamp = m5[confirmation_index]["timestamp"]

    if confirmation_timestamp in used_confirmation_timestamps:
        continue

    used_confirmation_timestamps.add(confirmation_timestamp)

    entry = signal["entry"]
    sl = signal["sl"]
    tp1 = signal["tp1"]
    tp2 = signal["tp2"]
    tp3 = signal["tp3"]

    outcome = None
    rr = 0.0

    for future in m5[
        confirmation_index + 1:
        confirmation_index + LOOKAHEAD + 1
    ]:

        if direction == "BUY":

            hit_sl = future["low"] <= sl
            hit_tp3 = future["high"] >= tp3
            hit_tp2 = future["high"] >= tp2
            hit_tp1 = future["high"] >= tp1

        else:

            hit_sl = future["high"] >= sl
            hit_tp3 = future["low"] <= tp3
            hit_tp2 = future["low"] <= tp2
            hit_tp1 = future["low"] <= tp1

        # Conservative rule when SL and TP are both touched
        # in the same candle: SL wins.
        if hit_sl:
            outcome = "SL"
            rr = -1.0
            break

        if hit_tp3:
            outcome = "TP3"
            rr = 3.0
            break

        if hit_tp2:
            outcome = "TP2"
            rr = 2.0
            break

        if hit_tp1:
            outcome = "TP1"
            rr = 1.5
            break

    if outcome is None:
        outcome = "TIMEOUT"
        rr = 0.0

    results.append({
        "direction": direction,
        "time": m5[confirmation_index]["datetime"],
        "entry": entry,
        "sl": sl,
        "outcome": outcome,
        "rr": rr,
        "confirmations": signal["confirmations"],
    })


print("=" * 70)
print("📊 RÉSULTATS")
print("=" * 70)

print(f"Configurations H1/M15      : {setups}")
print(f"Signaux confirmés M5        : {len(results)}")

for direction in ("BUY", "SELL"):
    data = [r for r in results if r["direction"] == direction]
    print(f"{direction:25} : {len(data)}")

for outcome in ("TP1", "TP2", "TP3", "SL", "TIMEOUT"):
    data = [r for r in results if r["outcome"] == outcome]
    print(f"{outcome:25} : {len(data)}")

if results:
    total_rr = sum(r["rr"] for r in results)
    win_count = sum(r["rr"] > 0 for r in results)
    win_rate = win_count / len(results) * 100

    print()
    print(f"RR total                   : {total_rr:.2f}R")
    print(f"RR moyen                   : {total_rr / len(results):.3f}R")
    print(f"Taux de réussite           : {win_rate:.1f}%")

    print()
    print("Derniers signaux :")

    for r in results[-10:]:
        print(
            f"{r['time']} | "
            f"{r['direction']} | "
            f"{r['outcome']} | "
            f"{r['rr']:+.1f}R | "
            f"{r['confirmations']}"
        )
else:
    print()
    print("❌ Aucun signal confirmé.")

print()
print("=" * 70)
print("🎯 BACKTEST FINAL TERMINÉ")
print("=" * 70)
