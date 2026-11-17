FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY src ./src
COPY db ./db
COPY configs ./configs
COPY data/feeds ./data/feeds
COPY docs/TARGETS.md ./docs/TARGETS.md
CMD ["sh", "-c", "python -m src.migrate && uvicorn src.api.app:app --host 0.0.0.0 --port 8000"]
