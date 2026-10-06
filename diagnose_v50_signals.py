from v50_data import get_candles
from v50_smc import (
    detect_structure,
    detect_premium_discount,
    confirm_m5,
)

COUNT = 1000
STEP = 5
MIN_M5 = 200


def candles_before(candles, timestamp):
    return [c for c in candles if c["timestamp"] < timestamp]


print("🔬 DIAGNOSTIC DES CONDITIONS SMC V50")
print("=" * 65)
print("⚠️ Données historiques réelles Deriv.")
print("⚠️ Alignement par timestamp réel.")
print("⚠️ Aucun trade réel.")
print()

print("📥 Téléchargement...")
h1 = get_candles("H1", COUNT)
m15 = get_candles("M15", COUNT)
m5 = get_candles("M5", COUNT)

print(f"✅ H1  : {len(h1)}")
print(f"✅ M15 : {len(m15)}")
print(f"✅ M5  : {len(m5)}")
print()

stats = {
    "points": 0,
    "h1_bull": 0,
    "h1_bear": 0,
    "m15_bull": 0,
    "m15_bear": 0,
    "same_bull": 0,
    "same_bear": 0,
    "m15_discount": 0,
    "m15_premium": 0,
    "m5_buy_structure": 0,
    "m5_sell_structure": 0,
    "buy_complete": 0,
    "sell_complete": 0,
}

examples = {
    "buy": [],
    "sell": [],
}


for i in range(MIN_M5, len(m5) - 1, STEP):

    current = m5[i]
    timestamp = current["timestamp"]

    h1_data = candles_before(h1, timestamp)
    m15_data = candles_before(m15, timestamp)
    m5_data = m5[:i + 1]

    if len(h1_data) < 50 or len(m15_data) < 100:
        continue

    stats["points"] += 1

    h1_structure = detect_structure(h1_data)
    m15_structure = detect_structure(m15_data)

    h1_trend = h1_structure["trend"]
    m15_trend = m15_structure["trend"]

    if h1_trend == "HAUSSIER":
        stats["h1_bull"] += 1

    if h1_trend == "BAISSIER":
        stats["h1_bear"] += 1

    if m15_trend == "HAUSSIER":
        stats["m15_bull"] += 1

    if m15_trend == "BAISSIER":
        stats["m15_bear"] += 1

    zone = detect_premium_discount(m15_data)

    if h1_trend == "HAUSSIER" and m15_trend == "HAUSSIER":
        stats["same_bull"] += 1

        if zone["zone"] == "DISCOUNT":
            stats["m15_discount"] += 1

            confirmations = confirm_m5(m5_data, "BUY")

            if confirmations:
                stats["m5_buy_structure"] += 1

                if len(examples["buy"]) < 5:
                    examples["buy"].append(
                        (current, confirmations, zone)
                    )

    if h1_trend == "BAISSIER" and m15_trend == "BAISSIER":
        stats["same_bear"] += 1

        if zone["zone"] == "PREMIUM":
            stats["m15_premium"] += 1

            confirmations = confirm_m5(m5_data, "SELL")

            if confirmations:
                stats["m5_sell_structure"] += 1

                if len(examples["sell"]) < 5:
                    examples["sell"].append(
                        (current, confirmations, zone)
                    )


print("=" * 65)
print("📊 RÉSULTATS DU DIAGNOSTIC")
print("=" * 65)

print(f"Points historiques analysés : {stats['points']}")
print()

print("🔎 TENDANCE")
print(f"H1 HAUSSIER                 : {stats['h1_bull']}")
print(f"H1 BAISSIER                 : {stats['h1_bear']}")
print(f"M15 HAUSSIER                : {stats['m15_bull']}")
print(f"M15 BAISSIER                : {stats['m15_bear']}")
print()

print("🔗 ALIGNEMENT H1 + M15")
print(f"H1/M15 HAUSSIER             : {stats['same_bull']}")
print(f"H1/M15 BAISSIER             : {stats['same_bear']}")
print()

print("🎯 ZONES")
print(f"Alignés haussiers + DISCOUNT: {stats['m15_discount']}")
print(f"Alignés baissiers + PREMIUM : {stats['m15_premium']}")
print()

print("🧱 CONFIRMATION STRUCTURELLE M5")
print(f"BUY confirmé par BOS/CHOCH  : {stats['m5_buy_structure']}")
print(f"SELL confirmé par BOS/CHOCH : {stats['m5_sell_structure']}")
print()

print("📋 EXEMPLES BUY")
if examples["buy"]:
    for candle, confirmations, zone in examples["buy"]:
        print(
            f"{candle['datetime']} | "
            f"confirmations={confirmations} | "
            f"zone={zone['zone']}"
        )
else:
    print("Aucun.")

print()

print("📋 EXEMPLES SELL")
if examples["sell"]:
    for candle, confirmations, zone in examples["sell"]:
        print(
            f"{candle['datetime']} | "
            f"confirmations={confirmations} | "
            f"zone={zone['zone']}"
        )
else:
    print("Aucun.")

print()
print("=" * 65)
print("🎯 DIAGNOSTIC TERMINÉ")
print("=" * 65)
