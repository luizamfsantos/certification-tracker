FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
RUN uv sync --no-dev

COPY . .

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app/main.py", "--server.headless", "true", "--server.port", "8501", "--server.address", "0.0.0.0"]
