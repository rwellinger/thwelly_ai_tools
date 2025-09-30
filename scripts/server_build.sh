#!/bin/zsh

# shellcheck disable=SC2164
cd ../aiproxysrv
docker-compose down aiproxy-app celery-worker
docker-compose build --no-cache
