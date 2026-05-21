#Building submodule
FROM python:3.12-slim AS wheel-builder
WORKDIR /build
COPY GarminDB/ .
RUN pip install --no-cache-dir build && python -m build --wheel --outdir /dist

#Building final image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends coreutils libfaketime && \
    ln -s /usr/lib/*/faketime/libfaketime.so.1 /usr/lib/libfaketime.so.1 && \
    echo "/usr/lib/libfaketime.so.1" > /etc/ld.so.preload && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=wheel-builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir fastapi uvicorn matplotlib mcp /tmp/*.whl && rm /tmp/*.whl

COPY src /app

EXPOSE 8000
EXPOSE 8001

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 & python -m mcp_server.main & wait"]
