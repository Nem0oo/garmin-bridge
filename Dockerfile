FROM python:3.11-slim
ENV PIPX_HOME=/root/.local
ENV PATH=$PIPX_HOME/bin:$PATH

RUN apt update && apt install -y pipx coreutils libfaketime && \
ln -s /usr/lib/*/faketime/libfaketime.so.1 /usr/lib/libfaketime.so.1 && \
echo "/usr/lib/libfaketime.so.1" > /etc/ld.so.preload

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn  matplotlib mcp
RUN pipx install garmindb

COPY src /app

# Exposer les ports
#api
EXPOSE 8000
#mcp
EXPOSE 8001


CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 & python -m mcp.main & wait"]