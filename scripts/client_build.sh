#!/bin/zsh

# shellcheck disable=SC2164
cd ../forwardproxy
docker-compose down

rm -rf html/aiwebui

# shellcheck disable=SC2164
cd ../aiwebui
ng build --configuration production --base-href /aiwebui/
