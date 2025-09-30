#!/bin/zsh

# shellcheck disable=SC2164
cd ../aiproxysrv
docker-compose down celery-worker
docker-compose down aiproxy-app
docker-compose build --no-cache
