import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def parse_timestamp(value):
    """Parse an ISO-8601 timestamp, including timestamps ending in Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def reconcile():
    payments = {}
    base_dir = Path(__file__).resolve().parent

    with (base_dir / "payments.jsonl").open(
        encoding="utf-8"
    ) as file:
        for line in file:
            try:
                event = json.loads(line)

                txn_id = event.get("txn_id")
                if not txn_id:
                    continue

                timestamp = parse_timestamp(event["ts"])

                # Keep the latest attempt for each transaction.
                previous = payments.get(txn_id)
                if previous is None or timestamp >= previous[0]:
                    payments[txn_id] = (timestamp, event)

            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                # Ignore malformed or incomplete records.
                continue

    successful = [
        event
        for _, event in payments.values()
        if event.get("status") == "success"
    ]

    for event in successful:
        try:
            Decimal(str(event["amount"]))
        except Exception:
            print("Invalid amount:", repr(event.get("amount")))
            print("Event:", event)

    total = sum(
    (
        Decimal(str(event["amount"]).replace(",", ""))
        for event in successful
    ),
    Decimal("0"),
)
    count = len(successful)

    with (base_dir / "expected.txt").open(encoding="utf-8") as file:
        expected = int(file.read().strip())

    if count != expected:
        print(
            f"Check failed: counted {count} successful payments, "
            f"expected {expected}."
        )
        print(
            "Something in the data isn't being handled "
            "the way the README describes."
        )
        return

    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")


if __name__ == "__main__":
    reconcile()
