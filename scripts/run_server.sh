#!/bin/zsh

cd ../aiproxysrv
docker-compose up -d

wait 5

docker ps
