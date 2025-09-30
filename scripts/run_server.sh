#!/bin/zsh

cd ../aiproxysrv
docker-compose up -d

docker-compose celery-worker up -d
docker-compose aiproxysrv up -d

docker ps
