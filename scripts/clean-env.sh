#!/bin/bash

echo "Stopping and removing all Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null
docker rm $(docker ps -aq) 2>/dev/null

echo "Removing all Docker images..."
docker rmi $(docker images -aq) 2>/dev/null

echo "Pruning Docker volumes, networks, and build cache..."
docker volume prune -f 2>/dev/null
docker network prune -f 2>/dev/null
docker builder prune -f 2>/dev/null || true

echo "Cleaning up any dangling images..."
docker image prune -f 2>/dev/null

echo "Environment clean-up complete."
