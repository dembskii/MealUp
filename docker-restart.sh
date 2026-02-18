#!/bin/bash

docker compose down -v
sleep 2
docker compose up -d --build auth-redis auth-service api-gateway shared-postgres-db user-service recipe-service shared-mongo-db frontend workout-service forum-service 