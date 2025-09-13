#!/bin/zsh

# shellcheck disable=SC2164
cd revproxy/html

rm -rf aiwebui

# shellcheck disable=SC2164
cd ../../aiwebui

ng build --configuration production --base-href /aiwebui/

cd ../revproxy

docker-compose down
