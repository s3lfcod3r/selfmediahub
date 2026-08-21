FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

ENV PORT=8092     DATA_DIR=/data     PYTHONUNBUFFERED=1     PUID=99     PGID=100

EXPOSE 8092
VOLUME ["/data"]

# Startet als root, uebereignet /data an PUID:PGID und gibt die Rechte ab,
# BEVOR die Anwendung Anfragen annimmt (siehe app/entrypoint.py).
CMD ["python", "-m", "app.entrypoint"]
