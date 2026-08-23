# Data Query

A small, runnable data-querying project that generates a deterministic JSON analytics report from a SQLite sales database. It is an application/data utility, not an infrastructure-as-code project.

## What it does

The solver reads three related tables (`customers`, `orders`, and `order_items`), validates that the required schema is present, and produces:

- overall customer/order/revenue totals;
- the top five customers by completed-order revenue; and
- completed revenue grouped by month.

Cancelled and pending orders are excluded from revenue. Invalid input fails fast and does not create a partial report.

## Requirements

- Python 3.11+
- `pip` for development/test dependencies
- Docker (optional)

All test dependencies are pinned in `requirements.lock`. The runtime solution itself uses only the Python standard library.

## Fresh-clone setup

```bash
git clone https://github.com/saurabho7222/data-query.git
cd data-query
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --no-deps -r requirements.lock
sh task/tests/test.sh
```

The final command is the canonical test command and should pass from a clean clone.

## Run locally

Create the included sample database:

```bash
python3 task/examples/create_sample_db.py .local/sample.db
```

Generate a report:

```bash
python3 task/solution/solve.py \
  --input .local/sample.db \
  --output .local/report.json
cat .local/report.json
```

`task/solution/solve.sh` is also available for environments that provide the default paths `/app/input.db` and `/app/output.json`. Override them with `INPUT_DB` and `OUTPUT_JSON` environment variables when needed.

## Run with Docker

Build the image from the repository root:

```bash
docker build -f task/environment/Dockerfile -t data-query .
```

Create local sample input, then mount it into the container:

```bash
mkdir -p .local
python3 task/examples/create_sample_db.py .local/input.db
docker run --rm \
  -v "$PWD/.local:/data" \
  data-query \
  python3 task/solution/solve.py --input /data/input.db --output /data/output.json
cat .local/output.json
```

Run the complete test suite inside the same image:

```bash
docker run --rm data-query sh task/tests/test.sh
```

## Input contract

The SQLite database must contain:

```text
customers(id, name, region)
orders(id, customer_id, order_date, status)
order_items(order_id, product, quantity, unit_price)
```

Only `orders.status = 'completed'` contributes to revenue. See `task/instruction.md` for the exact output contract.

## Project structure

- `task/solution/solve.py` — SQLite validation, queries, and JSON report generation.
- `task/solution/solve.sh` — portable entry point using default `/app` paths.
- `task/tests/test_outputs.py` — behavioral tests with real SQLite fixtures and assertions.
- `task/tests/test.sh` — fresh-clone test command.
- `task/examples/create_sample_db.py` — creates a runnable sample database.
- `task/environment/Dockerfile` — reproducible Python test/runtime image.
- `requirements.txt` — direct development dependency manifest.
- `requirements.lock` — exact resolved test dependency versions.
- `.github/workflows/ci.yml` — runs tests and Docker verification on every push and pull request.

## Development workflow

Keep changes small and reviewable. Feature or bug-fix commits should include the tests that demonstrate the new behavior. Avoid mixing unrelated formatting, refactors, and functionality in one commit.
