#!/bin/zsh

cd ../aiproxysrv

docker-compose up celery-worker aiproxy-app -d
docker ps
