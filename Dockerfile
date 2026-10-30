FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uvicorn "mcp<2" "garminconnect[workout]"

COPY src /app

EXPOSE 8001

CMD ["python", "-m", "mcp_server.main"]
