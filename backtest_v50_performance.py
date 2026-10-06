from datetime import datetime
from zoneinfo import ZoneInfo

from v50_data import get_candles
from v50_smc import build_signal


COUNT = 1000
LOOKAHEAD = 60
STEP = 5
MIN_H1 = 50
MIN_M15 = 100
MIN_M5 = 200


print("📊 BACKTEST PERFORMANCE — SMC V50")
print("=" * 65)
print("⚠️ Données historiques réelles Deriv.")
print("⚠️ Alignement par timestamp réel.")
print("⚠️ Aucun trade réel.")
print("⚠️ Aucun message Telegram.")
print()


# ============================================================
# DONNÉES
# ============================================================

print("📥 Téléchargement des données...")

h1 = get_candles("H1", COUNT)
m15 = get_candles("M15", COUNT)
m5 = get_candles("M5", COUNT)

print(f"✅ H1  : {len(h1)} bougies")
print(f"✅ M15 : {len(m15)} bougies")
print(f"✅ M5  : {len(m5)} bougies")
print()


# ============================================================
# ALIGNEMENT TEMPOREL
# ============================================================

def candles_before(candles, timestamp):
    return [
        candle
        for candle in candles
        if candle["timestamp"] < timestamp
    ]


def candles_up_to(candles, timestamp):
    return [
        candle
        for candle in candles
        if candle["timestamp"] <= timestamp
    ]


# ============================================================
# RÉSULTATS
# ============================================================

signals = []

stats = {
    "BUY": 0,
    "SELL": 0,
    "TP1": 0,
    "TP2": 0,
    "TP3": 0,
    "SL": 0,
    "TIMEOUT": 0,
    "AMBIGUOUS": 0,
}


tested_points = 0


# ============================================================
# BACKTEST
# ============================================================

print("🔎 Analyse des points historiques...")
print()

for i in range(MIN_M5, len(m5) - LOOKAHEAD, STEP):

    current = m5[i]
    timestamp = current["timestamp"]

    # --------------------------------------------------------
    # IMPORTANT :
    # On utilise uniquement les bougies H1/M15 terminées
    # AVANT l'ouverture de la bougie M5 étudiée.
    # --------------------------------------------------------

    h1_data = candles_before(
        h1,
        timestamp,
    )

    m15_data = candles_before(
        m15,
        timestamp,
    )

    m5_data = m5[:i + 1]

    if len(h1_data) < MIN_H1:
        continue

    if len(m15_data) < MIN_M15:
        continue

    if len(m5_data) < MIN_M5:
        continue

    tested_points += 1

    signal = build_signal(
        h1_data,
        m15_data,
        m5_data,
    )

    if signal is None:
        continue

    direction = signal["direction"]

    entry = signal["entry"]
    sl = signal["sl"]
    tp1 = signal["tp1"]
    tp2 = signal["tp2"]
    tp3 = signal["tp3"]

    future = m5[i + 1:i + 1 + LOOKAHEAD]

    result = "TIMEOUT"
    exit_price = future[-1]["close"]
    exit_timestamp = future[-1]["timestamp"]

    for candle in future:

        high = candle["high"]
        low = candle["low"]

        if direction == "BUY":

            hit_sl = low <= sl
            hit_tp1 = high >= tp1
            hit_tp2 = high >= tp2
            hit_tp3 = high >= tp3

            # Si SL et TP sont touchés dans la même bougie,
            # l'ordre réel est inconnu avec des données OHLC.
            if hit_sl and (hit_tp1 or hit_tp2 or hit_tp3):
                result = "AMBIGUOUS"
                exit_price = entry
                exit_timestamp = candle["timestamp"]
                break

            if hit_tp3:
                result = "TP3"
                exit_price = tp3
                exit_timestamp = candle["timestamp"]
                break

            if hit_tp2:
                result = "TP2"
                exit_price = tp2
                exit_timestamp = candle["timestamp"]
                break

            if hit_tp1:
                result = "TP1"
                exit_price = tp1
                exit_timestamp = candle["timestamp"]
                break

            if hit_sl:
                result = "SL"
                exit_price = sl
                exit_timestamp = candle["timestamp"]
                break

        else:

            hit_sl = high >= sl
            hit_tp1 = low <= tp1
            hit_tp2 = low <= tp2
            hit_tp3 = low <= tp3

            if hit_sl and (hit_tp1 or hit_tp2 or hit_tp3):
                result = "AMBIGUOUS"
                exit_price = entry
                exit_timestamp = candle["timestamp"]
                break

            if hit_tp3:
                result = "TP3"
                exit_price = tp3
                exit_timestamp = candle["timestamp"]
                break

            if hit_tp2:
                result = "TP2"
                exit_price = tp2
                exit_timestamp = candle["timestamp"]
                break

            if hit_tp1:
                result = "TP1"
                exit_price = tp1
                exit_timestamp = candle["timestamp"]
                break

            if hit_sl:
                result = "SL"
                exit_price = sl
                exit_timestamp = candle["timestamp"]
                break

    stats[direction] += 1
    stats[result] += 1

    signals.append({
        "timestamp": timestamp,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "result": result,
        "exit_price": exit_price,
        "exit_timestamp": exit_timestamp,
        "confirmations": signal["confirmations"],
        "zone": signal["m15_zone"],
    })


# ============================================================
# RÉSULTATS
# ============================================================

print("=" * 65)
print("📈 RÉSULTATS")
print("=" * 65)

print(f"Points historiques testés : {tested_points}")
print(f"Signaux trouvés            : {len(signals)}")
print(f"BUY                        : {stats['BUY']}")
print(f"SELL                       : {stats['SELL']}")
print()

print("🎯 SORTIES")
print(f"TP1                        : {stats['TP1']}")
print(f"TP2                        : {stats['TP2']}")
print(f"TP3                        : {stats['TP3']}")
print(f"SL                         : {stats['SL']}")
print(f"TIMEOUT                    : {stats['TIMEOUT']}")
print(f"AMBIGUOUS                  : {stats['AMBIGUOUS']}")
print()


# ============================================================
# PERFORMANCE
# ============================================================

resolved = (
    stats["TP1"]
    + stats["TP2"]
    + stats["TP3"]
    + stats["SL"]
)

wins = (
    stats["TP1"]
    + stats["TP2"]
    + stats["TP3"]
)

print("📊 PERFORMANCE")
print()

if resolved > 0:
    winrate = wins / resolved * 100
    print(f"Taux de réussite : {winrate:.2f}%")
else:
    print("Taux de réussite : impossible")

print(f"Gagnants         : {wins}")
print(f"Perdants         : {stats['SL']}")
print(f"Non résolus      : {len(signals) - resolved}")

print()


# ============================================================
# RR THÉORIQUE
# ============================================================

rr_values = {
    "TP1": 1.5,
    "TP2": 2.0,
    "TP3": 3.0,
    "SL": -1.0,
    "TIMEOUT": 0.0,
    "AMBIGUOUS": 0.0,
}

total_r = sum(
    rr_values[s["result"]]
    for s in signals
)

print("💰 RR THÉORIQUE")
print(f"Résultat total : {total_r:.2f}R")

if signals:
    print(
        f"Moyenne/trade : "
        f"{total_r / len(signals):.3f}R"
    )
else:
    print("Moyenne/trade : impossible")

print()


# ============================================================
# DÉTAIL
# ============================================================

print("=" * 65)
print("📋 DÉTAIL DES SIGNAUX")
print("=" * 65)

if not signals:
    print("ℹ️ Aucun signal historique trouvé.")
else:

    for number, signal in enumerate(signals, 1):

        dt = datetime.fromtimestamp(
            signal["timestamp"],
            ZoneInfo("Indian/Antananarivo"),
        )

        print()
        print(f"--- Signal {number} ---")
        print(
            f"Date          : "
            f"{dt.strftime('%d/%m/%Y %H:%M')}"
        )
        print(
            f"Direction     : {signal['direction']}"
        )
        print(
            f"Entry         : {signal['entry']:.4f}"
        )
        print(
            f"SL            : {signal['sl']:.4f}"
        )
        print(
            f"TP1           : {signal['tp1']:.4f}"
        )
        print(
            f"TP2           : {signal['tp2']:.4f}"
        )
        print(
            f"TP3           : {signal['tp3']:.4f}"
        )
        print(
            f"Zone M15      : {signal['zone']}"
        )
        print(
            "Confirmation  : "
            + ", ".join(signal["confirmations"])
        )
        print(
            f"Résultat      : {signal['result']}"
        )


print()
print("=" * 65)
print("🧪 BACKTEST PERFORMANCE TERMINÉ")
print("=" * 65)
print(
    "⚠️ Un backtest historique ne garantit pas "
    "les performances futures."
)
