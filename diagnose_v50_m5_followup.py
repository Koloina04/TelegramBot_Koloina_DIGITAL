from v50_data import get_candles
from v50_smc import (
    detect_structure,
    detect_premium_discount,
    detect_liquidity_sweep,
)

COUNT = 1000
STEP = 5
MIN_M5 = 200
LOOKAHEAD = 12

print("🔬 DIAGNOSTIC M5 — CONFIRMATION APRÈS CONFIGURATION")
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


def expected_confirmation(structure, direction):
    if direction == "SELL":
        if structure["bos"] == "BOS_BAISSIER":
            return "BOS_BAISSIER"
        if structure["choch"] == "CHOCH_BAISSIER":
            return "CHOCH_BAISSIER"

    if direction == "BUY":
        if structure["bos"] == "BOS_HAUSSIER":
            return "BOS_HAUSSIER"
        if structure["choch"] == "CHOCH_HAUSSIER":
            return "CHOCH_HAUSSIER"

    return None


candidates = []

for i in range(MIN_M5, len(m5) - LOOKAHEAD - 1, STEP):

    current = m5[i]
    timestamp = current["timestamp"]

    h1_data = candles_before(h1, timestamp)
    m15_data = candles_before(m15, timestamp)
    m5_data = m5[:i + 1]

    if len(h1_data) < 50 or len(m15_data) < 100:
        continue

    h1_structure = detect_structure(h1_data)
    m15_structure = detect_structure(m15_data)

    zone = detect_premium_discount(m15_data)

    direction = None

    if (
        h1_structure["trend"] == "BAISSIER"
        and m15_structure["trend"] == "BAISSIER"
        and zone["zone"] == "PREMIUM"
    ):
        direction = "SELL"

    elif (
        h1_structure["trend"] == "HAUSSIER"
        and m15_structure["trend"] == "HAUSSIER"
        and zone["zone"] == "DISCOUNT"
    ):
        direction = "BUY"

    if direction:
        candidates.append((i, direction, current, m5_data, zone))


print("=" * 70)
print(f"🎯 CONFIGURATIONS : {len(candidates)}")
print(f"🔭 FENÊTRE DE CONFIRMATION : {LOOKAHEAD} bougies M5")
print("=" * 70)

for number, (i, direction, current, m5_data, zone) in enumerate(
    candidates, 1
):

    print()
    print("-" * 70)
    print(f"📌 CONFIGURATION #{number}")
    print("-" * 70)

    print(f"Date       : {current['datetime']}")
    print(f"Direction  : {direction}")
    print(f"Prix       : {current['close']}")
    print(f"Zone       : {zone['zone']}")

    initial = detect_structure(m5_data)
    initial_sweep = detect_liquidity_sweep(m5_data)

    print()
    print("M5 AU MOMENT DE LA CONFIGURATION")
    print(f"Tendance   : {initial['trend']}")
    print(f"BOS        : {initial['bos']}")
    print(f"CHOCH      : {initial['choch']}")
    print(f"Sweep      : {initial_sweep}")

    found = False

    print()
    print("ÉVOLUTION DES 12 BOUGIES SUIVANTES")

    for step in range(1, LOOKAHEAD + 1):

        future_data = m5[:i + step + 1]
        future = future_data[-1]

        structure = detect_structure(future_data)
        sweep = detect_liquidity_sweep(future_data)

        confirmation = expected_confirmation(
            structure,
            direction,
        )

        if confirmation:
            print(
                f"  +{step:02d} | "
                f"{future['datetime']} | "
                f"prix={future['close']} | "
                f"tendance={structure['trend']} | "
                f"CONFIRMATION={confirmation} | "
                f"niveau={structure['broken_level']}"
            )
            found = True
            break

        if sweep:
            expected_sweep = (
                sweep["type"] == "SWEEP_HIGH"
                if direction == "SELL"
                else sweep["type"] == "SWEEP_LOW"
            )

            if expected_sweep:
                print(
                    f"  +{step:02d} | "
                    f"{future['datetime']} | "
                    f"prix={future['close']} | "
                    f"SWEEP={sweep['type']} | "
                    f"niveau={sweep['level']}"
                )

    if not found:
        print("  ❌ Aucune confirmation structurelle dans la fenêtre.")


print()
print("=" * 70)
print("🎯 DIAGNOSTIC FOLLOW-UP TERMINÉ")
print("=" * 70)
