FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VI_DATA_DIR=/app/data VI_WORKFLOW_ENGINE=langgraph
COPY backend/requirements.txt backend/requirements-agent.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements-agent.txt
COPY backend /app/backend
COPY frontend/standalone /app/frontend/standalone
RUN mkdir -p /app/data
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
