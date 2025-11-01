# pelmers.com self-hosting setup

This repo contains scripts and config files I use to set up my server.

## Pre-requisites
Run setup_server.py

### ghost-docker
Hosts pelmers.com blog
```
docker compose build && docker compose up -d
```

### rybbit
Hosts page count analytics for the other sites
```
docker compose build && docker compose up -d
```

### streetwarp-docker
Hosts streetwarp.com
```
docker compose build && docker compose up -d
```

### gpx-splice-redirect-docker
Hosts the redirect handler for GPX Splice's Strava login feature.
```
docker compose build && docker compose up -d
```