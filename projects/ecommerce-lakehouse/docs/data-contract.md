# Data Contract

The generated source contract represents the minimum fields required by the platform. All amounts use USD in the simulated business context and must be non-negative.

## Core entities

| Entity | Primary key | Required fields |
|---|---|---|
| Customers | `customer_id` | `email`, `country`, `registered_date` |
| Products | `product_id` | `product_name`, `category`, `unit_price` |
| Orders | `order_id` | `customer_id`, `order_date`, `order_status` |
| Order items | `order_item_id` | `order_id`, `product_id`, `quantity`, `unit_price` |
| Payments | `payment_id` | `order_id`, `payment_status`, `amount` |
| Shipments | `shipment_id` | `order_id`, `promised_delivery_date`, `shipping_cost` |
| Refunds | `refund_id` | `order_id`, `refund_date`, `refund_status`, `amount` |

## Accepted domains

- Order status: `delivered`, `shipped`, `cancelled`
- Payment status: `paid`, `refunded`
- Shipment status: `delivered`, `in_transit`, `cancelled`
- Refund status: `processed`

## Quality rules

- Primary keys are unique and not null.
- Foreign keys resolve to their parent entity.
- Quantities are positive.
- Amounts and shipping costs are non-negative.
- Delivery dates can be null only for shipments that are not delivered.
- `gold_fact_order` remains at one row per order.

## Change policy

Adding a required field or changing an accepted domain is a contract change. Update the generator, Silver projection, dbt source documentation, tests and README in the same pull request.
