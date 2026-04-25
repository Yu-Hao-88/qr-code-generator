FROM python:3.12.13-slim-bookworm

WORKDIR /app

ENV TZ=Asia/Taipei

RUN apt-get update \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "routes/main.py"]

