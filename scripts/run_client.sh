#!/bin/zsh

cd ../forwardproxy
docker-compose up -d

wait 5

docker ps

