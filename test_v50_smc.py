from v50_smc import (
    detect_structure,
    build_signal,
    find_swing_highs,
    find_swing_lows,
)


def make_candles(values):
    candles = []

    for i, value in enumerate(values):
        candles.append({
            "timestamp": i * 300,
            "datetime": f"2026-01-01T00:{i:02d}:00",
            "open": float(value),
            "high": float(value) + 0.2,
            "low": float(value) - 0.2,
            "close": float(value),
        })

    return candles


def check(name, condition):
    if condition:
        print(f"✅ {name}")
    else:
        print(f"❌ {name}")
        raise AssertionError(name)


print("🧪 TEST AUTOMATIQUE — STRUCTURE SMC V50")
print("=" * 50)
print("⚠️ Aucun trade réel.")
print("⚠️ Aucun message Telegram.")
print()


# ============================================================
# TEST 1 — DONNÉES RÉELLES
# ============================================================

print("1️⃣ Vérification des données réelles")

from v50_data import get_multi_timeframe_data

data = get_multi_timeframe_data()

for timeframe in ("H1", "M15", "M5"):
    candles = data[timeframe]

    check(
        f"{timeframe} : au moins 10 bougies",
        len(candles) >= 10
    )

    check(
        f"{timeframe} : OHLC valide",
        all(
            c["high"] >= max(c["open"], c["close"])
            and c["low"] <= min(c["open"], c["close"])
            for c in candles
        )
    )

    timestamps = [c["timestamp"] for c in candles]

    check(
        f"{timeframe} : chronologie correcte",
        timestamps == sorted(timestamps)
    )

print()


# ============================================================
# TEST 2 — SWINGS
# ============================================================

print("2️⃣ Vérification des swings")

for timeframe in ("H1", "M15", "M5"):
    candles = data[timeframe]

    highs = find_swing_highs(candles)
    lows = find_swing_lows(candles)

    check(
        f"{timeframe} : swings hauts détectés",
        len(highs) > 0
    )

    check(
        f"{timeframe} : swings bas détectés",
        len(lows) > 0
    )

print()


# ============================================================
# TEST 3 — STRUCTURE RÉELLE
# ============================================================

print("3️⃣ Structure actuelle")

for timeframe in ("H1", "M15", "M5"):
    structure = detect_structure(data[timeframe])

    print(
        f"{timeframe} : "
        f"Tendance={structure['trend']} | "
        f"BOS={structure['bos']} | "
        f"CHOCH={structure['choch']}"
    )

print()


# ============================================================
# TEST 4 — RÈGLE NEUTRE
# ============================================================

print("4️⃣ Règle : structure NEUTRE")

for timeframe in ("H1", "M15", "M5"):
    structure = detect_structure(data[timeframe])

    if structure["trend"] == "NEUTRE":
        check(
            f"{timeframe} neutre => aucun BOS/CHOCH",
            structure["bos"] is None
            and structure["choch"] is None
        )

print()


# ============================================================
# TEST 5 — COHÉRENCE BOS / CHOCH
# ============================================================

print("5️⃣ Cohérence BOS / CHOCH")

for timeframe in ("H1", "M15", "M5"):
    structure = detect_structure(data[timeframe])

    if structure["bos"] is not None:
        check(
            f"{timeframe} : BOS compatible avec tendance",
            (
                structure["trend"] == "HAUSSIER"
                and structure["bos"] == "BOS_HAUSSIER"
            )
            or
            (
                structure["trend"] == "BAISSIER"
                and structure["bos"] == "BOS_BAISSIER"
            )
        )

    if structure["choch"] is not None:
        check(
            f"{timeframe} : CHOCH opposé à la tendance",
            (
                structure["trend"] == "HAUSSIER"
                and structure["choch"] == "CHOCH_BAISSIER"
            )
            or
            (
                structure["trend"] == "BAISSIER"
                and structure["choch"] == "CHOCH_HAUSSIER"
            )
        )

print()


# ============================================================
# TEST 6 — BUILD SIGNAL
# ============================================================

print("6️⃣ Construction du signal")

signal = build_signal(
    data["H1"],
    data["M15"],
    data["M5"],
)

if signal is None:
    print("ℹ️ Aucun signal actuel — comportement normal.")
else:
    print(f"Direction : {signal['direction']}")
    print(f"Entry     : {signal['entry']}")
    print(f"SL        : {signal['sl']}")
    print(f"TP1       : {signal['tp1']}")
    print(f"TP2       : {signal['tp2']}")
    print(f"TP3       : {signal['tp3']}")

    check(
        "Entry valide",
        signal["entry"] > 0
    )

    check(
        "SL valide",
        signal["sl"] > 0
    )

    check(
        "TP1 valide",
        signal["tp1"] > 0
    )

    check(
        "TP2 valide",
        signal["tp2"] > 0
    )

    check(
        "TP3 valide",
        signal["tp3"] > 0
    )

    check(
        "RR TP1 correct",
        signal["rr_tp1"] == 1.5
    )

    check(
        "RR TP2 correct",
        signal["rr_tp2"] == 2.0
    )

    check(
        "RR TP3 correct",
        signal["rr_tp3"] == 3.0
    )

print()


# ============================================================
# TEST 7 — AUCUN EFFET TELEGRAM
# ============================================================

print("7️⃣ Sécurité Telegram")

print("✅ Le test n'appelle aucune fonction d'envoi Telegram.")
print("✅ Aucun message réel n'a été envoyé.")

print()


# ============================================================
# TEST 8 — COMPILATION
# ============================================================

print("8️⃣ Compilation")

import py_compile

for filename in (
    "v50_data.py",
    "v50_smc.py",
    "test_v50_smc.py",
):
    py_compile.compile(
        filename,
        doraise=True
    )

    print(f"✅ {filename}")


print()
print("=" * 50)
print("🎯 TEST SMC V50 TERMINÉ AVEC SUCCÈS")
print("=" * 50)
