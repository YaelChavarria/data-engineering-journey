"""Generate source and target snapshots for a deterministic migration review."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


COUNTRIES = ["US", "CA", "MX", "GB"]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_snapshots(
    source_dir: Path,
    target_dir: Path,
    account_count: int = 60,
    scenario: str = "review",
) -> dict[str, int]:
    """Create a legacy source and a post-migration target snapshot.

    The review scenario introduces controlled discrepancies so the control room
    can demonstrate a real HOLD decision. The clean scenario is useful for
    testing the go-live path.
    """
    if scenario not in {"review", "clean"}:
        raise ValueError("scenario must be 'review' or 'clean'")
    source_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    accounts: list[dict] = []
    invoices: list[dict] = []
    transactions: list[dict] = []
    contacts: list[dict] = []
    for account_id in range(1, account_count + 1):
        accounts.append(
            {
                "account_id": account_id,
                "account_name": f"Meridian Account {account_id:03d}",
                "country": COUNTRIES[account_id % len(COUNTRIES)],
                "created_date": (date(2023, 1, 1) + timedelta(days=account_id * 4)).isoformat(),
                "monthly_value": f"{99 + (account_id % 4) * 150:.2f}",
            }
        )
        for month_number in range(1, 4):
            invoices.append(
                {
                    "invoice_id": f"INV-{account_id:03d}-{month_number}",
                    "account_id": account_id,
                    "invoice_date": date(2025, month_number, 1).isoformat(),
                    "amount": f"{99 + (account_id % 4) * 150:.2f}",
                    "invoice_status": "paid" if (account_id + month_number) % 7 else "overdue",
                }
            )
        for transaction_number in range(1, 5):
            transactions.append(
                {
                    "transaction_id": f"TXN-{account_id:03d}-{transaction_number}",
                    "account_id": account_id,
                    "transaction_date": (date(2025, 1, 5) + timedelta(days=(account_id + transaction_number) % 80)).isoformat(),
                    "amount": f"{25 + ((account_id + transaction_number) % 8) * 10:.2f}",
                    "transaction_type": "charge" if transaction_number % 3 else "credit",
                }
            )
        for contact_number in range(1, 4):
            contacts.append(
                {
                    "contact_id": f"CON-{account_id:03d}-{contact_number}",
                    "account_id": account_id,
                    "email": f"contact{account_id:03d}{contact_number}@meridian.example",
                    "country": COUNTRIES[(account_id + contact_number) % len(COUNTRIES)],
                    "contact_status": "active" if contact_number < 3 else "inactive",
                }
            )

    target_accounts = [dict(row) for row in accounts]
    target_invoices = [dict(row) for row in invoices]
    target_transactions = [dict(row) for row in transactions]
    target_contacts = [dict(row) for row in contacts]
    if scenario == "review":
        target_accounts = [row for row in target_accounts if row["account_id"] != 17]
        target_accounts.append(dict(next(row for row in accounts if row["account_id"] == 5)));
        target_invoices = [row for row in target_invoices if row["invoice_id"] != "INV-021-2"]
        target_invoices.append(dict(next(row for row in invoices if row["invoice_id"] == "INV-034-1")))
        for row in target_invoices:
            if row["invoice_id"] == "INV-028-2":
                row["amount"] = f"{float(row['amount']) + 35:.2f}"
        target_contacts = [row for row in target_contacts if row["contact_id"] not in {"CON-012-2", "CON-041-1"}]

    schemas = {
        "accounts": ["account_id", "account_name", "country", "created_date", "monthly_value"],
        "invoices": ["invoice_id", "account_id", "invoice_date", "amount", "invoice_status"],
        "transactions": ["transaction_id", "account_id", "transaction_date", "amount", "transaction_type"],
        "contacts": ["contact_id", "account_id", "email", "country", "contact_status"],
    }
    rows_by_table = {
        "accounts": (accounts, target_accounts),
        "invoices": (invoices, target_invoices),
        "transactions": (transactions, target_transactions),
        "contacts": (contacts, target_contacts),
    }
    for table, (source_rows, target_rows) in rows_by_table.items():
        _write_csv(source_dir / f"{table}.csv", schemas[table], source_rows)
        _write_csv(target_dir / f"{table}.csv", schemas[table], target_rows)
    return {table: len(source_rows) for table, (source_rows, _) in rows_by_table.items()}
