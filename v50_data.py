import json
import websocket
from datetime import datetime
from zoneinfo import ZoneInfo


DERIV_WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
V50_SYMBOL = "R_50"

TIMEFRAMES = {
    "M5": 300,
    "M15": 900,
    "H1": 3600,
}


def get_candles(timeframe, count=200):
    """
    Récupère des bougies OHLC réelles du Volatility 50 Index
    depuis l'API publique Deriv.

    timeframe : M5, M15 ou H1
    count     : nombre de bougies souhaitées
    """

    if timeframe not in TIMEFRAMES:
        raise ValueError(
            f"Timeframe invalide : {timeframe}. "
            f"Valeurs autorisées : {', '.join(TIMEFRAMES)}"
        )

    if not isinstance(count, int) or count < 10 or count > 1000:
        raise ValueError("count doit être un entier entre 10 et 1000.")

    ws = None

    try:
        ws = websocket.create_connection(
            DERIV_WS_URL,
            timeout=20
        )

        ws.send(json.dumps({
            "ticks_history": V50_SYMBOL,
            "count": count,
            "end": "latest",
            "style": "candles",
            "granularity": TIMEFRAMES[timeframe],
            "req_id": TIMEFRAMES[timeframe],
        }))

        response = json.loads(ws.recv())

        if "error" in response:
            error = response["error"]
            raise RuntimeError(
                f"Deriv : {error.get('code', 'UNKNOWN')} - "
                f"{error.get('message', 'Erreur inconnue')}"
            )

        raw_candles = response.get("candles")

        if not raw_candles:
            raise RuntimeError(
                "Deriv n'a retourné aucune bougie."
            )

        candles = []

        for candle in raw_candles:
            candles.append({
                "timestamp": int(candle["epoch"]),
                "datetime": datetime.fromtimestamp(
                    int(candle["epoch"]),
                    ZoneInfo("Indian/Antananarivo")
                ).isoformat(),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
            })

        return candles

    except websocket.WebSocketTimeoutException as e:
        raise RuntimeError(
            f"Timeout de connexion à Deriv : {e}"
        ) from e

    except websocket.WebSocketException as e:
        raise RuntimeError(
            f"Erreur WebSocket Deriv : {e}"
        ) from e

    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def get_multi_timeframe_data():
    """
    Récupère les données nécessaires à l'analyse SMC :
    H1 = contexte
    M15 = structure
    M5 = précision
    """

    return {
        "H1": get_candles("H1", 200),
        "M15": get_candles("M15", 200),
        "M5": get_candles("M5", 200),
    }


if __name__ == "__main__":
    print("📈 Test des données Volatility 50 Index")
    print(f"Symbole Deriv : {V50_SYMBOL}")
    print()

    for timeframe in ("H1", "M15", "M5"):
        candles = get_candles(timeframe, 10)

        print(
            f"✅ {timeframe} : "
            f"{len(candles)} bougies"
        )

        last = candles[-1]

        print(
            f"   Dernière bougie : {last['datetime']}"
        )
        print(
            f"   O={last['open']} "
            f"H={last['high']} "
            f"L={last['low']} "
            f"C={last['close']}"
        )

        print()

    print("✅ Module v50_data.py opérationnel.")
