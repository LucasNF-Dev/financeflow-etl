FROM python:3.12.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.lock pyproject.toml README.md ./
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY src ./src
COPY mock_api ./mock_api
COPY tests ./tests
RUN python -m pip install --no-cache-dir --no-build-isolation --no-deps .
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "mock_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
