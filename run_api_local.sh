#!/bin/bash

# 設置腳本在任何命令失敗時停止執行
set -o errexit

docker rmi qr_code_generator || true
docker build . -t qr_code_generator
docker stop qr_code_generator_c || true
docker rm qr_code_generator_c || true
docker run --rm \
	-v .:/app \
	qr_code_generator alembic -c configs/alembic.ini upgrade head

docker run -it -d -p 8000:8000 \
	-m 4096mb \
	--add-host=host.docker.internal:host-gateway \
	-v .:/app \
	--name qr_code_generator_c qr_code_generator python routes/main.py
