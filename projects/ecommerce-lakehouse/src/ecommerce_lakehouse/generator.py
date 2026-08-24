"""Create a small, deterministic e-commerce source system."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


PRODUCTS = [
    (1, "Wireless Keyboard", "electronics", 49.90),
    (2, "USB-C Hub", "electronics", 29.90),
    (3, "Mechanical Mouse", "electronics", 39.90),
    (4, "Running Shoes", "sports", 89.00),
    (5, "Yoga Mat", "sports", 24.50),
    (6, "Coffee Grinder", "home", 74.00),
    (7, "Desk Lamp", "home", 32.00),
    (8, "Notebook Set", "stationery", 12.90),
]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_source_data(source_dir: Path, order_count: int = 36) -> dict[str, int]:
    """Generate source CSVs without randomness, so every run is reproducible."""
    source_dir.mkdir(parents=True, exist_ok=True)

    customers = [
        {
            "customer_id": customer_id,
            "full_name": f"Customer {customer_id:02d}",
            "email": f"customer{customer_id:02d}@example.com",
            "country": ["ES", "PT", "FR", "DE"][customer_id % 4],
            "registered_date": (date(2024, 9, 1) + timedelta(days=customer_id * 3)).isoformat(),
        }
        for customer_id in range(1, 13)
    ]
    products = [
        {
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "unit_price": unit_price,
        }
        for product_id, product_name, category, unit_price in PRODUCTS
    ]

    orders: list[dict] = []
    order_items: list[dict] = []
    payments: list[dict] = []
    for order_id in range(1, order_count + 1):
        customer_id = ((order_id * 7) % 12) + 1
        order_date = date(2025, 1, 1) + timedelta(days=(order_id * 3) % 90)
        status = "cancelled" if order_id % 11 == 0 else ("shipped" if order_id % 4 == 0 else "delivered")
        item_count = (order_id % 3) + 1
        total = 0.0
        for line_number in range(1, item_count + 1):
            product_id = ((order_id + line_number * 2) % len(PRODUCTS)) + 1
            quantity = (order_id + line_number) % 3 + 1
            unit_price = PRODUCTS[product_id - 1][3]
            total += quantity * unit_price
            order_items.append(
                {
                    "order_item_id": f"{order_id}-{line_number}",
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": f"{unit_price:.2f}",
                }
            )
        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.isoformat(),
                "order_status": status,
                "shipping_country": ["ES", "PT", "FR", "DE"][order_id % 4],
            }
        )
        payments.append(
            {
                "payment_id": f"PAY-{order_id:04d}",
                "order_id": order_id,
                "payment_method": ["card", "paypal", "bank_transfer"][order_id % 3],
                "payment_status": "refunded" if status == "cancelled" else "paid",
                "amount": f"{0 if status == 'cancelled' else total:.2f}",
            }
        )

    _write_csv(
        source_dir / "customers.csv",
        ["customer_id", "full_name", "email", "country", "registered_date"],
        customers,
    )
    _write_csv(
        source_dir / "products.csv",
        ["product_id", "product_name", "category", "unit_price"],
        products,
    )
    _write_csv(
        source_dir / "orders.csv",
        ["order_id", "customer_id", "order_date", "order_status", "shipping_country"],
        orders,
    )
    _write_csv(
        source_dir / "order_items.csv",
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price"],
        order_items,
    )
    _write_csv(
        source_dir / "payments.csv",
        ["payment_id", "order_id", "payment_method", "payment_status", "amount"],
        payments,
    )
    return {
        "customers": len(customers),
        "products": len(products),
        "orders": len(orders),
        "order_items": len(order_items),
        "payments": len(payments),
    }
