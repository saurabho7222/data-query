FROM public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock requirements.txt README.md project-metadata.json docker-compose.yml ./
COPY .devcontainer ./.devcontainer
COPY .github/workflows/release.yml ./.github/workflows/release.yml
COPY src ./src
RUN python3 -m pip install --break-system-packages --no-cache-dir .

COPY requirements-dev.txt ./
RUN python3 -m pip install --break-system-packages --no-cache-dir -r requirements-dev.txt

COPY examples ./examples
COPY tests ./tests

EXPOSE 8000

CMD ["data-query", "--help"]
