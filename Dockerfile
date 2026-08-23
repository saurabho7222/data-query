FROM python:3.11.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements.lock /workspace/requirements.lock
RUN python -m pip install --no-cache-dir --no-deps -r /workspace/requirements.lock

COPY task /workspace/task

CMD ["python3", "task/solution/solve.py", "--help"]
