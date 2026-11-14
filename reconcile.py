#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (from the README):
- Every attempt of a payment shares its txn_id; only the latest attempt (by ts) counts. The file is not in time
  order, so "latest" comes from ts, not from the line's position.
- A payment is collected only if its latest attempt is "success".
- Lines that aren't valid JSON, and events without a txn_id, are skipped.
- Amounts are naira and come as numbers or as strings with thousands separators ("12,345.67"); both are parsed
  exactly with Decimal, so the total has no float rounding drift.
"""
import json
from datetime import datetime
from decimal import Decimal


def parse_amount(value):
    if isinstance(value, bool):
        raise ValueError(f"not an amount: {value!r}")
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    return Decimal(str(value).replace(",", "").strip())


def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def latest_attempts(path):
    latest = {}
    skipped = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            txn_id = event.get("txn_id") if isinstance(event, dict) else None
            if not txn_id:
                skipped += 1
                continue
            ts = parse_ts(event["ts"])
            current = latest.get(txn_id)
            if current is None or ts > current[0]:
                latest[txn_id] = (ts, event)
    return latest, skipped


def main():
    latest, skipped = latest_attempts("payments.jsonl")

    total = Decimal("0")
    count = 0
    for _, event in latest.values():
        if event["status"] == "success":
            total += parse_amount(event["amount"])
            count += 1

    with open("expected.txt") as f:
        expected = int(f.read().strip())

    print(f"Payments: {len(latest)}, skipped lines: {skipped}, collected: NGN {total:,.2f}")
    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{round(total)}")


if __name__ == "__main__":
    main()
