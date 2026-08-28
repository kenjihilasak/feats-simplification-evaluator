FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements-server.txt /tmp/requirements-server.txt
RUN pip install --no-cache-dir -r /tmp/requirements-server.txt

RUN mkdir -p /app/phase4a_gold_standard
COPY __init__.py /app/phase4a_gold_standard/__init__.py
COPY backend /app/phase4a_gold_standard/backend
COPY web /app/phase4a_gold_standard/web
COPY deploy/railway/start.sh /usr/local/bin/phase4a-start
RUN chmod 0755 /usr/local/bin/phase4a-start

EXPOSE 8000
CMD ["/usr/local/bin/phase4a-start"]
