FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/medievaia ./medievaia

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn medievaia.api:app --host 0.0.0.0 --port ${PORT}"]
