from v50_data import get_candles
from v50_smc import detect_structure, build_signal


TIMEFRAMES = ("H1", "M15", "M5")
COUNT = 500
STEP = 10
MIN_CANDLES = 200


print("📊 BACKTEST HISTORIQUE — SMC V50")
print("=" * 60)
print("⚠️ Données réelles Deriv.")
print("⚠️ Aucun trade réel.")
print("⚠️ Aucun message Telegram.")
print()


# ============================================================
# RÉCUPÉRATION DES DONNÉES
# ============================================================

data = {}

for timeframe in TIMEFRAMES:
    print(f"📥 Téléchargement {timeframe}...")

    candles = get_candles(
        timeframe,
        COUNT
    )

    data[timeframe] = candles

    print(
        f"✅ {timeframe} : "
        f"{len(candles)} bougies"
    )

print()


# ============================================================
# BACKTEST
# ============================================================

signals = []
tested = 0

trend_counts = {
    "HAUSSIER": 0,
    "BAISSIER": 0,
    "NEUTRE": 0,
}

bos_counts = {
    "BOS_HAUSSIER": 0,
    "BOS_BAISSIER": 0,
}

choch_counts = {
    "CHOCH_HAUSSIER": 0,
    "CHOCH_BAISSIER": 0,
}


# On utilise les mêmes positions historiques
# dans les trois timeframes.
max_index = min(
    len(data["H1"]),
    len(data["M15"]),
    len(data["M5"]),
)

for end in range(
    MIN_CANDLES,
    max_index + 1,
    STEP
):
    h1 = data["H1"][:end]
    m15 = data["M15"][:end]
    m5 = data["M5"][:end]

    tested += 1

    # --------------------------------------------------------
    # STRUCTURES
    # --------------------------------------------------------

    structures = {
        "H1": detect_structure(h1),
        "M15": detect_structure(m15),
        "M5": detect_structure(m5),
    }

    for structure in structures.values():
        trend_counts[structure["trend"]] += 1

        if structure["bos"] in bos_counts:
            bos_counts[structure["bos"]] += 1

        if structure["choch"] in choch_counts:
            choch_counts[structure["choch"]] += 1

    # --------------------------------------------------------
    # SIGNAL
    # --------------------------------------------------------

    signal = build_signal(
        h1,
        m15,
        m5,
    )

    if signal is not None:
        signals.append({
            "index": end,
            "direction": signal["direction"],
            "entry": signal["entry"],
            "sl": signal["sl"],
            "tp1": signal["tp1"],
            "tp2": signal["tp2"],
            "tp3": signal["tp3"],
            "confirmations": signal["confirmations"],
            "zone": signal["m15_zone"],
        })


# ============================================================
# RÉSULTATS
# ============================================================

print("=" * 60)
print("📈 RÉSULTATS")
print("=" * 60)

print(f"Fenêtres testées : {tested}")
print()

print("📊 TENDANCES")
print(
    f"HAUSSIER : {trend_counts['HAUSSIER']}"
)
print(
    f"BAISSIER : {trend_counts['BAISSIER']}"
)
print(
    f"NEUTRE   : {trend_counts['NEUTRE']}"
)

print()

print("🔀 BOS")
print(
    f"BOS_HAUSSIER : {bos_counts['BOS_HAUSSIER']}"
)
print(
    f"BOS_BAISSIER : {bos_counts['BOS_BAISSIER']}"
)

print()

print("🔄 CHOCH")
print(
    f"CHOCH_HAUSSIER : {choch_counts['CHOCH_HAUSSIER']}"
)
print(
    f"CHOCH_BAISSIER : {choch_counts['CHOCH_BAISSIER']}"
)

print()

print("🎯 SIGNAUX")

buy_count = sum(
    s["direction"] == "BUY"
    for s in signals
)

sell_count = sum(
    s["direction"] == "SELL"
    for s in signals
)

print(f"Total : {len(signals)}")
print(f"BUY   : {buy_count}")
print(f"SELL  : {sell_count}")

print()

# ============================================================
# AFFICHAGE DES SIGNAUX
# ============================================================

if not signals:
    print("ℹ️ Aucun signal historique trouvé.")
else:
    print("📋 Signaux détectés :")
    print()

    for i, signal in enumerate(signals, 1):
        print(f"--- Signal {i} ---")
        print(
            f"Index          : {signal['index']}"
        )
        print(
            f"Direction      : {signal['direction']}"
        )
        print(
            f"Entry          : {signal['entry']:.4f}"
        )
        print(
            f"SL             : {signal['sl']:.4f}"
        )
        print(
            f"TP1            : {signal['tp1']:.4f}"
        )
        print(
            f"TP2            : {signal['tp2']:.4f}"
        )
        print(
            f"TP3            : {signal['tp3']:.4f}"
        )
        print(
            f"Zone M15       : {signal['zone']}"
        )
        print(
            "Confirmations  : "
            + ", ".join(signal["confirmations"])
        )
        print()


# ============================================================
# VÉRIFICATIONS DE COHÉRENCE
# ============================================================

print("=" * 60)
print("🧪 VÉRIFICATIONS")
print("=" * 60)

errors = 0

for signal in signals:

    entry = signal["entry"]
    sl = signal["sl"]
    tp1 = signal["tp1"]
    tp2 = signal["tp2"]
    tp3 = signal["tp3"]

    if signal["direction"] == "BUY":

        if not (sl < entry < tp1 < tp2 < tp3):
            print(
                "❌ Ordre de prix invalide pour BUY :",
                signal
            )
            errors += 1

    elif signal["direction"] == "SELL":

        if not (sl > entry > tp1 > tp2 > tp3):
            print(
                "❌ Ordre de prix invalide pour SELL :",
                signal
            )
            errors += 1


if errors == 0:
    print("✅ Tous les Entry / SL / TP sont cohérents.")
else:
    print(
        f"❌ {errors} erreur(s) Entry / SL / TP."
    )

print()
print("=" * 60)

if errors == 0:
    print("🎯 BACKTEST TERMINÉ — AUCUNE INCOHÉRENCE DÉTECTÉE")
else:
    print("⚠️ BACKTEST TERMINÉ — CORRECTIONS NÉCESSAIRES")

print("=" * 60)
