# Data Querying and Databases

A small, self-contained workspace for building and validating data-querying and SQL-focused tasks.

## Project structure

- `task/instruction.md` — describes the data/querying problem, inputs, and required outputs.
- `task/task.toml` — project metadata and runtime/resource settings.
- `task/environment/Dockerfile` — reproducible execution and test environment.
- `task/solution/solve.sh` — entry point for a reference implementation.
- `task/tests/test.sh` — test runner.
- `task/tests/test_outputs.py` — output validation tests.

## Getting started

1. Define the problem and expected output contract in `task/instruction.md`.
2. Add any required runtime dependencies to `task/environment/Dockerfile`.
3. Implement the reference solution under `task/solution/`.
4. Add validation coverage under `task/tests/`.
5. Update `task/task.toml` with the project-specific metadata and resource requirements.

Keep inputs, outputs, and verification rules explicit so the project can be reproduced and tested consistently.
