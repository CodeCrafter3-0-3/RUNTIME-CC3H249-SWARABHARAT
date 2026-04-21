FROM python:3.11-slim
WORKDIR /app

# Install minimal build deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY BACKEND/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . /app
ENV PYTHONPATH=/app/BACKEND
EXPOSE 5000
CMD ["gunicorn", "BACKEND.wsgi:application", "-w", "2", "-b", "0.0.0.0:5000"]
