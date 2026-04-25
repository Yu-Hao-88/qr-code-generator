#!/bin/bash

# 設置腳本在任何命令失敗時停止執行
set -o errexit

docker rmi qr_code_generator || true
docker build . -t qr_code_generator
docker run --rm \
	-v .:/app \
	qr_code_generator alembic -c configs/alembic.ini upgrade head

docker compose -f run_api_local_docker_compose.yml down
docker compose -f run_api_local_docker_compose.yml up
