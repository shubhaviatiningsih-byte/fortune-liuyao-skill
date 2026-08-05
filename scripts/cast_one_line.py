"""Generate one three-coin Liuyao line with a cryptographic random source."""

from __future__ import annotations

import argparse
import json
import secrets


LABELS = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}


def cast_one(position: int) -> dict[str, object]:
    coins = "".join("正" if secrets.randbits(1) else "反" for _ in range(3))
    value = sum(3 if side == "正" else 2 for side in coins)
    return {
        "position": position,
        "positionName": ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")[position - 1],
        "coins": coins,
        "value": value,
        "label": LABELS[value],
        "randomSource": "python_secrets",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one Liuyao line")
    parser.add_argument("--position", required=True, type=int, choices=range(1, 7))
    args = parser.parse_args()
    print(json.dumps(cast_one(args.position), ensure_ascii=False))


if __name__ == "__main__":
    main()
