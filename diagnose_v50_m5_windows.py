from v50_data import get_candles
from v50_smc import (
    detect_structure,
    detect_premium_discount,
    detect_liquidity_sweep,
)

COUNT = 1000
STEP = 5
MIN_M5 = 200
LOOKAHEADS = [12, 24, 48, 72]

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

for i in range(MIN_M5, len(m5) - 73, STEP):
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
        candidates.append((i, direction, current))

print("=" * 70)
print(f"🎯 CONFIGURATIONS : {len(candidates)}")
print("=" * 70)

for lookahead in LOOKAHEADS:

    print()
    print(f"🔭 FENÊTRE : {lookahead} bougies M5 ({lookahead * 5} minutes)")
    print("-" * 70)

    confirmations = 0
    sweeps = 0
    confirmation_steps = []

    for i, direction, current in candidates:

        found_confirmation = False

        for step in range(1, lookahead + 1):

            future_data = m5[:i + step + 1]
            structure = detect_structure(future_data)
            sweep = detect_liquidity_sweep(future_data)

            if sweep:
                expected_sweep = (
                    sweep["type"] == "SWEEP_HIGH"
                    if direction == "SELL"
                    else sweep["type"] == "SWEEP_LOW"
                )

                if expected_sweep:
                    sweeps += 1

            confirmation = expected_confirmation(
                structure,
                direction,
            )

            if confirmation:
                confirmations += 1
                confirmation_steps.append(step)
                found_confirmation = True
                break

    print(f"Configurations              : {len(candidates)}")
    print(f"Confirmation structurelle    : {confirmations}")
    print(f"Configurations avec sweep   : {sweeps}")

    if confirmation_steps:
        print(
            "Délai moyen confirmation    : "
            f"{sum(confirmation_steps) / len(confirmation_steps):.1f} bougies M5"
        )
        print(
            "Délai minimum               : "
            f"{min(confirmation_steps)} bougie(s)"
        )
        print(
            "Délai maximum               : "
            f"{max(confirmation_steps)} bougies"
        )
    else:
        print("Délai confirmation           : aucune")

print()
print("=" * 70)
print("🎯 TEST DES FENÊTRES M5 TERMINÉ")
print("=" * 70)


print()
print("=" * 70)
print("🎯 DIAGNOSTIC FOLLOW-UP TERMINÉ")
print("=" * 70)
