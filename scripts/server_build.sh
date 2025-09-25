#!/bin/zsh

# shellcheck disable=SC2164
cd ../aiproxysrv
docker-compose down
docker-compose build --no-cache
