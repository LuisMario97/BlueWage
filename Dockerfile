FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements-production.txt backend/requirements-production.txt
RUN pip install --no-cache-dir -r backend/requirements-production.txt
COPY backend/ backend/
COPY bluewage_pipeline_cuantil.joblib ./
RUN useradd --create-home appuser
USER appuser
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
