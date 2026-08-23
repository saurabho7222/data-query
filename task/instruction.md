Build a JSON analytics report from a SQLite sales database.

The default input is `/app/input.db` and the default output is `/app/output.json`. The command-line implementation may also accept explicit input and output paths for local testing.

The input database must contain these tables and columns:

- `customers(id, name, region)`
- `orders(id, customer_id, order_date, status)`
- `order_items(order_id, product, quantity, unit_price)`

Only orders whose `status` is exactly `completed` contribute to revenue. Revenue is the sum of `quantity * unit_price` across matching order items. Monetary values in the output must be rounded to two decimal places.

`/app/output.json` must contain:

- `schema_version`: integer `1`.
- `summary`: `total_customers`, `total_orders`, `completed_orders`, and `completed_revenue`.
- `top_customers`: up to five customers with completed orders, ordered by completed revenue descending and then customer id ascending. Each item contains `customer_id`, `name`, `region`, `orders`, and `revenue`.
- `monthly_revenue`: completed-order totals grouped by the first seven characters of `order_date` (`YYYY-MM`), ordered ascending. Each item contains `month`, `orders`, and `revenue`.

A valid database with the required schema but no rows must succeed with zero-valued summary fields and empty aggregate lists. Missing files, non-SQLite inputs, and databases missing required tables or columns must fail with a non-zero exit status and must not create the output file.
