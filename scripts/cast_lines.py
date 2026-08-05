"""Generate or normalize six bottom-up Liuyao line values."""

from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path


COIN_VALUE = {"正": 3, "反": 2}
LINE_LABEL = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}


def _manual_cast(raw: str) -> list[dict[str, object]]:
    rounds = [part.strip().replace(" ", "") for part in raw.replace("，", ",").replace("/", ",").split(",")]
    rounds = [part for part in rounds if part]
    if len(rounds) != 6:
        raise ValueError("manual casting requires exactly six rounds from bottom line to top line")
    result = []
    for index, coins in enumerate(rounds, start=1):
        if len(coins) != 3 or any(coin not in COIN_VALUE for coin in coins):
            raise ValueError(f"round {index} must contain exactly three characters using 正 or 反")
        value = sum(COIN_VALUE[coin] for coin in coins)
        result.append({"round": index, "coins": coins, "value": value, "label": LINE_LABEL[value]})
    return result


def _automatic_cast() -> list[dict[str, object]]:
    result = []
    for index in range(1, 7):
        coins = "".join("正" if secrets.randbits(1) else "反" for _ in range(3))
        value = sum(COIN_VALUE[coin] for coin in coins)
        result.append({"round": index, "coins": coins, "value": value, "label": LINE_LABEL[value]})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Create six Liuyao lines in bottom-up order")
    parser.add_argument("--mode", required=True, choices=("auto", "manual"))
    parser.add_argument("--manual", help="Six slash-separated coin rounds, for example 正反反/正正反/反反反/正反反/正正正/正正反")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.mode == "manual" and not args.manual:
        parser.error("--manual is required when --mode manual is selected")
    rounds = _manual_cast(args.manual) if args.mode == "manual" else _automatic_cast()
    payload = {
        "schemaVersion": "fortune-liuyao-casting.v1",
        "mode": args.mode,
        "order": "bottom_up",
        "coinConvention": {"正": 3, "反": 2},
        "randomSource": "python_secrets" if args.mode == "auto" else "external_manual",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "rounds": rounds,
        "linesBottomUp": [row["value"] for row in rounds],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
