#!/bin/zsh

# shellcheck disable=SC2164
cd revproxy/html

rm -rf aiwebui

# shellcheck disable=SC2164
cd ../../aiwebui

npm run build:prod

cd ../revproxy

docker-compose down
