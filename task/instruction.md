Read the SQLite database at `/app/input.db` and write a deterministic analytics report to `/app/output.json`.

The input database must contain these columns:
- `customers(id, name, region)`
- `orders(id, customer_id, order_date, status)`
- `order_items(order_id, product, quantity, unit_price)`

Only orders whose `status` is `completed` contribute to revenue. Revenue for an item is `quantity * unit_price`.

The JSON report must contain:
- `schema_version`: integer `2`;
- `filters`: the applied `region`, `start_date`, `end_date`, and `top_limit` values;
- `summary`: `total_customers`, `total_orders`, `completed_orders`, and `completed_revenue`;
- `top_customers`: up to `top_limit` customers ordered by completed revenue descending, then customer id ascending. Each row has `customer_id`, `name`, `region`, `orders`, and `revenue`;
- `monthly_revenue`: completed revenue grouped by `YYYY-MM`, ordered ascending. Each row has `month`, `orders`, and `revenue`.

Money values must be rounded to two decimal places. Invalid input must fail without leaving a partial output file.

The CLI may optionally filter by customer region and inclusive start/end order dates, change the top-customer limit, and write CSV exports for `top_customers` and `monthly_revenue`.
