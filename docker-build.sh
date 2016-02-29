#!/bin/sh
docker build -t frankh/catan-server -f Dockerfile.server . && \
docker build -t frankh/catan-client -f Dockerfile.client .