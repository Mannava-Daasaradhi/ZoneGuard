FROM python:3.12-slim

WORKDIR /app

# Configure pip
RUN pip config set global.timeout 120 && \
    pip config set global.index-url https://pypi.org/simple/

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
