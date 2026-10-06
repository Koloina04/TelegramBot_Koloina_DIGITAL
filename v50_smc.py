from v50_data import get_multi_timeframe_data


# ============================================================
# SWINGS
# ============================================================

def find_swing_highs(candles, left=2, right=2):
    swings = []

    for i in range(left, len(candles) - right):
        high = candles[i]["high"]

        if (
            all(high > candles[j]["high"] for j in range(i - left, i))
            and
            all(high >= candles[j]["high"] for j in range(i + 1, i + right + 1))
        ):
            swings.append({
                "index": i,
                "price": high,
                "timestamp": candles[i]["timestamp"],
            })

    return swings


def find_swing_lows(candles, left=2, right=2):
    swings = []

    for i in range(left, len(candles) - right):
        low = candles[i]["low"]

        if (
            all(low < candles[j]["low"] for j in range(i - left, i))
            and
            all(low <= candles[j]["low"] for j in range(i + 1, i + right + 1))
        ):
            swings.append({
                "index": i,
                "price": low,
                "timestamp": candles[i]["timestamp"],
            })

    return swings


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_swings(highs, lows):
    classified_highs = []
    classified_lows = []

    for i, swing in enumerate(highs):
        item = dict(swing)

        if i == 0:
            item["label"] = "H"
        elif swing["price"] > highs[i - 1]["price"]:
            item["label"] = "HH"
        else:
            item["label"] = "LH"

        classified_highs.append(item)

    for i, swing in enumerate(lows):
        item = dict(swing)

        if i == 0:
            item["label"] = "L"
        elif swing["price"] > lows[i - 1]["price"]:
            item["label"] = "HL"
        else:
            item["label"] = "LL"

        classified_lows.append(item)

    return classified_highs, classified_lows


# ============================================================
# STRUCTURE
# ============================================================

def detect_structure(candles):
    highs = find_swing_highs(candles)
    lows = find_swing_lows(candles)

    classified_highs, classified_lows = classify_swings(
        highs,
        lows,
    )

    result = {
        "trend": "NEUTRE",
        "bos": None,
        "choch": None,
        "highs": classified_highs,
        "lows": classified_lows,
        "broken_level": None,
    }

    if len(classified_highs) < 2 or len(classified_lows) < 2:
        return result

    close = candles[-1]["close"]

    # --------------------------------------------------------
    # STRUCTURE RÉCENTE
    # --------------------------------------------------------

    last_high = classified_highs[-1]
    previous_high = classified_highs[-2]

    last_low = classified_lows[-1]
    previous_low = classified_lows[-2]

    higher_high = last_high["price"] > previous_high["price"]
    lower_high = last_high["price"] < previous_high["price"]

    higher_low = last_low["price"] > previous_low["price"]
    lower_low = last_low["price"] < previous_low["price"]

    # --------------------------------------------------------
    # TENDANCE
    # --------------------------------------------------------

    if higher_high and higher_low:
        trend = "HAUSSIER"

    elif lower_high and lower_low:
        trend = "BAISSIER"

    else:
        trend = "NEUTRE"

    result["trend"] = trend

    # --------------------------------------------------------
    # BOS / CHOCH
    #
    # On vérifie d'abord la cassure de structure.
    # Le CHOCH représente une cassure dans le sens opposé
    # à la structure précédente.
    # --------------------------------------------------------

    if trend == "HAUSSIER":

        # Continuation de la structure haussière.
        if close > last_high["price"]:
            result["bos"] = "BOS_HAUSSIER"
            result["broken_level"] = last_high["price"]

        # Rupture du dernier creux protégé.
        elif close < last_low["price"]:
            result["choch"] = "CHOCH_BAISSIER"
            result["broken_level"] = last_low["price"]

    elif trend == "BAISSIER":

        # Continuation de la structure baissière.
        if close < last_low["price"]:
            result["bos"] = "BOS_BAISSIER"
            result["broken_level"] = last_low["price"]

        # Rupture du dernier sommet protégé.
        elif close > last_high["price"]:
            result["choch"] = "CHOCH_HAUSSIER"
            result["broken_level"] = last_high["price"]

    else:
        # Une structure réellement neutre ne produit
        # pas automatiquement un BOS/CHOCH.
        result["bos"] = None
        result["choch"] = None

    return result


# ============================================================
# LIQUIDITÉ
# ============================================================

def detect_liquidity_sweep(candles, lookback=20):
    if len(candles) < lookback + 1:
        return None

    current = candles[-1]
    previous = candles[-lookback:-1]

    previous_high = max(c["high"] for c in previous)
    previous_low = min(c["low"] for c in previous)

    if (
        current["high"] > previous_high
        and current["close"] < previous_high
    ):
        return {
            "type": "SWEEP_HIGH",
            "price": current["high"],
            "level": previous_high,
        }

    if (
        current["low"] < previous_low
        and current["close"] > previous_low
    ):
        return {
            "type": "SWEEP_LOW",
            "price": current["low"],
            "level": previous_low,
        }

    return None


# ============================================================
# PREMIUM / DISCOUNT
# ============================================================

def detect_premium_discount(candles, lookback=50):
    data = candles[-lookback:]

    high = max(c["high"] for c in data)
    low = min(c["low"] for c in data)

    equilibrium = (high + low) / 2
    price = candles[-1]["close"]

    if price > equilibrium:
        zone = "PREMIUM"
    elif price < equilibrium:
        zone = "DISCOUNT"
    else:
        zone = "EQUILIBRE"

    return {
        "high": high,
        "low": low,
        "equilibrium": equilibrium,
        "zone": zone,
    }


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def detect_support_resistance(candles, lookback=50):
    data = candles[-lookback:]

    return {
        "support": min(c["low"] for c in data),
        "resistance": max(c["high"] for c in data),
    }


# ============================================================
# CONFIRMATION M5
# ============================================================

def confirm_m5(candles, direction):
    structure = detect_structure(candles)
    sweep = detect_liquidity_sweep(candles)

    confirmations = []

    if direction == "BUY":

        # Une entrée BUY exige obligatoirement une
        # confirmation structurelle M5.
        if structure["bos"] == "BOS_HAUSSIER":
            confirmations.append("BOS_HAUSSIER")

        elif structure["choch"] == "CHOCH_HAUSSIER":
            confirmations.append("CHOCH_HAUSSIER")

        # Le sweep est une confirmation supplémentaire,
        # jamais une raison suffisante à lui seul.
        if sweep and sweep["type"] == "SWEEP_LOW":
            confirmations.append("SWEEP_LOW")

    elif direction == "SELL":

        # Une entrée SELL exige obligatoirement une
        # confirmation structurelle M5.
        if structure["bos"] == "BOS_BAISSIER":
            confirmations.append("BOS_BAISSIER")

        elif structure["choch"] == "CHOCH_BAISSIER":
            confirmations.append("CHOCH_BAISSIER")

        # Le sweep est une confirmation supplémentaire,
        # jamais une raison suffisante à lui seul.
        if sweep and sweep["type"] == "SWEEP_HIGH":
            confirmations.append("SWEEP_HIGH")

    # --------------------------------------------------------
    # IMPORTANT :
    # Un sweep seul ne valide jamais une entrée.
    # --------------------------------------------------------

    has_structure_confirmation = any(
        confirmation in (
            "BOS_HAUSSIER",
            "BOS_BAISSIER",
            "CHOCH_HAUSSIER",
            "CHOCH_BAISSIER",
        )
        for confirmation in confirmations
    )

    if not has_structure_confirmation:
        return []

    return confirmations


# ============================================================
# SIGNAL
# ============================================================

def build_signal(h1_candles, m15_candles, m5_candles):
    h1 = detect_structure(h1_candles)
    m15 = detect_structure(m15_candles)
    m5 = detect_structure(m5_candles)

    m15_pd = detect_premium_discount(m15_candles)
    sr = detect_support_resistance(m15_candles)

    direction = None

    if (
        h1["trend"] == "HAUSSIER"
        and m15["trend"] == "HAUSSIER"
    ):
        direction = "BUY"

    elif (
        h1["trend"] == "BAISSIER"
        and m15["trend"] == "BAISSIER"
    ):
        direction = "SELL"

    if direction is None:
        return None

    # BUY en discount
    if direction == "BUY" and m15_pd["zone"] == "PREMIUM":
        return None

    # SELL en premium
    if direction == "SELL" and m15_pd["zone"] == "DISCOUNT":
        return None

    confirmations = confirm_m5(
        m5_candles,
        direction,
    )

    if not confirmations:
        return None

    entry = m5_candles[-1]["close"]
    recent = m5_candles[-10:]

    if direction == "BUY":
        sl = min(c["low"] for c in recent)
        risk = entry - sl

        if risk <= 0:
            return None

        tp1 = entry + risk * 1.5
        tp2 = entry + risk * 2.0
        tp3 = entry + risk * 3.0

    else:
        sl = max(c["high"] for c in recent)
        risk = sl - entry

        if risk <= 0:
            return None

        tp1 = entry - risk * 1.5
        tp2 = entry - risk * 2.0
        tp3 = entry - risk * 3.0

    return {
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "risk": risk,
        "rr_tp1": 1.5,
        "rr_tp2": 2.0,
        "rr_tp3": 3.0,
        "confirmations": confirmations,
        "h1_trend": h1["trend"],
        "m15_trend": m15["trend"],
        "m5_trend": m5["trend"],
        "m15_zone": m15_pd["zone"],
        "support": sr["support"],
        "resistance": sr["resistance"],
    }


# ============================================================
# ANALYSE COMPLÈTE
# ============================================================

def analyze_v50():
    data = get_multi_timeframe_data()

    h1 = detect_structure(data["H1"])
    m15 = detect_structure(data["M15"])
    m5 = detect_structure(data["M5"])

    signal = build_signal(
        data["H1"],
        data["M15"],
        data["M5"],
    )

    return {
        "H1": h1,
        "M15": m15,
        "M5": m5,
        "signal": signal,
        "price": data["M5"][-1]["close"],
        "timestamp": data["M5"][-1]["timestamp"],
    }


# ============================================================
# AFFICHAGE
# ============================================================

def format_price(value):
    return f"{value:.4f}"


def format_structure(name, structure):
    lines = [
        f"🔎 {name}",
        f"• Tendance : {structure['trend']}",
        f"• BOS : {structure['bos'] or 'Aucun'}",
        f"• CHOCH : {structure['choch'] or 'Aucun'}",
    ]

    if structure["broken_level"] is not None:
        lines.append(
            f"• Niveau cassé : {format_price(structure['broken_level'])}"
        )

    if structure["highs"]:
        lines.append(
            "• Sommets : "
            + " → ".join(
                x["label"]
                for x in structure["highs"][-4:]
            )
        )

    if structure["lows"]:
        lines.append(
            "• Creux : "
            + " → ".join(
                x["label"]
                for x in structure["lows"][-4:]
            )
        )

    return lines


def format_analysis(result):
    signal = result["signal"]

    lines = [
        "📈 ANALYSE VOLATILITY 50 INDEX",
        "",
        f"💰 Prix : {format_price(result['price'])}",
        "",
    ]

    lines.extend(
        format_structure("H1", result["H1"])
    )

    lines.append("")

    lines.extend(
        format_structure("M15", result["M15"])
    )

    lines.append("")

    lines.extend(
        format_structure("M5", result["M5"])
    )

    lines.append("")

    if signal is None:
        lines.extend([
            "⚪ SIGNAL",
            "AUCUNE CONFIGURATION VALIDE",
            "",
            "Les confirmations nécessaires ne sont pas toutes réunies.",
        ])

        return "\n".join(lines)

    lines.extend([
        "🎯 SIGNAL",
        f"• Direction : {signal['direction']}",
        f"• Entry : {format_price(signal['entry'])}",
        f"• SL : {format_price(signal['sl'])}",
        "",
        f"🎯 TP1 : {format_price(signal['tp1'])} | RR 1:{signal['rr_tp1']}",
        f"🎯 TP2 : {format_price(signal['tp2'])} | RR 1:{signal['rr_tp2']}",
        f"🎯 TP3 : {format_price(signal['tp3'])} | RR 1:{signal['rr_tp3']}",
        "",
        "✅ Confirmations :",
    ])

    for confirmation in signal["confirmations"]:
        lines.append(f"• {confirmation}")

    lines.extend([
        "",
        f"📊 Zone M15 : {signal['m15_zone']}",
        "",
        "🛑 Invalidation :",
    ])

    if signal["direction"] == "BUY":
        lines.append(
            f"Clôture sous {format_price(signal['sl'])}"
        )
    else:
        lines.append(
            f"Clôture au-dessus de {format_price(signal['sl'])}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print("📈 Analyse SMC V50 — BOS/CHOCH corrigé")
    print()

    result = analyze_v50()

    print(format_analysis(result))

    print()
    print("✅ Analyse SMC terminée.")
