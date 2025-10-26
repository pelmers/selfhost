# Minimal image to run the GPX Splice OAuth redirect helper
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Allow overriding the script ref at build time to pin to a commit for reproducible builds
# Example: docker build --build-arg SCRIPT_REF=main .
ARG SCRIPT_REF=main

WORKDIR /app

COPY GPXSpliceApp/gpxsplice_redirect_server.py /app/gpxsplice_redirect_server.py
COPY GPXSpliceApp/assets/favicon.ico /app/assets/favicon.ico

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

EXPOSE 9090

CMD ["python", "/app/gpxsplice_redirect_server.py", "--port", "9090"]
