#!/bin/zsh

# shellcheck disable=SC2164
cd forwardproxy/html

rm -rf aiwebui

# shellcheck disable=SC2164
cd ../../aiwebui

ng build --configuration production --base-href /aiwebui/

docker-compose down
