"""Generate a deterministic client export for a repeatable delivery demo."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


PLANS = [("starter", 99.0), ("growth", 249.0), ("scale", 699.0)]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_client_export(source_dir: Path, account_count: int = 24) -> dict[str, int]:
    """Generate a stable export from the fictional Atlas SaaS client."""
    source_dir.mkdir(parents=True, exist_ok=True)
    accounts: list[dict] = []
    invoices: list[dict] = []
    tickets: list[dict] = []
    events: list[dict] = []

    for account_id in range(1, account_count + 1):
        plan, monthly_value = PLANS[account_id % len(PLANS)]
        is_churned = account_id % 11 == 0
        is_trial = account_id % 4 == 0 and not is_churned
        status = "churned" if is_churned else ("trial" if is_trial else "active")
        signup_date = date(2025, 1, 1) + timedelta(days=account_id * 2)
        accounts.append(
            {
                "account_id": account_id,
                "account_name": f"Atlas Customer {account_id:02d}",
                "plan": plan,
                "country": ["US", "CA", "MX", "GB"][account_id % 4],
                "signup_date": signup_date.isoformat(),
                "account_status": status,
                "monthly_recurring_revenue": f"{0 if status != 'active' else monthly_value:.2f}",
            }
        )
        if status in ("active", "churned"):
            for month_number, invoice_date in enumerate(
                (date(2025, 1, 1), date(2025, 2, 1), date(2025, 3, 1)), start=1
            ):
                invoice_status = "overdue" if account_id % 7 == 0 and month_number == 3 else "paid"
                invoices.append(
                    {
                        "invoice_id": f"INV-{account_id:03d}-{month_number}",
                        "account_id": account_id,
                        "invoice_date": invoice_date.isoformat(),
                        "amount": f"{monthly_value:.2f}",
                        "invoice_status": invoice_status,
                    }
                )
        events.append(
            {
                "event_id": f"EVT-{account_id:03d}-created",
                "account_id": account_id,
                "event_date": signup_date.isoformat(),
                "event_type": "account_created",
            }
        )
        if is_trial:
            events.append(
                {
                    "event_id": f"EVT-{account_id:03d}-trial",
                    "account_id": account_id,
                    "event_date": (signup_date + timedelta(days=1)).isoformat(),
                    "event_type": "trial_started",
                }
            )
            if account_id % 8 != 0:
                events.append(
                    {
                        "event_id": f"EVT-{account_id:03d}-activated",
                        "account_id": account_id,
                        "event_date": (signup_date + timedelta(days=14)).isoformat(),
                        "event_type": "activated",
                    }
                )
        if is_churned:
            events.append(
                {
                    "event_id": f"EVT-{account_id:03d}-cancelled",
                    "account_id": account_id,
                    "event_date": "2025-03-20",
                    "event_type": "cancelled",
                }
            )
        for ticket_number in range(1, 4):
            created_date = date(2025, 1, 5) + timedelta(days=(account_id * 5 + ticket_number * 7) % 75)
            is_open = (account_id + ticket_number) % 6 == 0
            resolution_days = 3 if account_id % 4 == 0 else 1
            tickets.append(
                {
                    "ticket_id": f"TCK-{account_id:03d}-{ticket_number}",
                    "account_id": account_id,
                    "created_date": created_date.isoformat(),
                    "resolved_date": "" if is_open else (created_date + timedelta(days=resolution_days)).isoformat(),
                    "priority": ["low", "medium", "high"][ticket_number % 3],
                    "ticket_status": "open" if is_open else "resolved",
                }
            )

    _write_csv(
        source_dir / "accounts.csv",
        [
            "account_id",
            "account_name",
            "plan",
            "country",
            "signup_date",
            "account_status",
            "monthly_recurring_revenue",
        ],
        accounts,
    )
    _write_csv(
        source_dir / "invoices.csv",
        ["invoice_id", "account_id", "invoice_date", "amount", "invoice_status"],
        invoices,
    )
    _write_csv(
        source_dir / "support_tickets.csv",
        ["ticket_id", "account_id", "created_date", "resolved_date", "priority", "ticket_status"],
        tickets,
    )
    _write_csv(
        source_dir / "account_events.csv",
        ["event_id", "account_id", "event_date", "event_type"],
        events,
    )
    return {
        "accounts": len(accounts),
        "invoices": len(invoices),
        "support_tickets": len(tickets),
        "account_events": len(events),
    }
