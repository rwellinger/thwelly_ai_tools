#!/bin/zsh

cd ../aiproxysrv

docker-compose up celery-worker -d
docker-compose up aiproxy-app -d


docker ps
