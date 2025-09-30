#!/bin/zsh

# shellcheck disable=SC2164
cd ../aiproxysrv
docker-compose celery-worker down
docker-compose aiproxysrv down
docker-compose build --no-cache
