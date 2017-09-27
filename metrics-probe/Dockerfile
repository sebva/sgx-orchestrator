FROM python:3.6.2-alpine3.6

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apk update && \
    apk add python3-dev build-base linux-headers && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del python3-dev build-base linux-headers

COPY *.py ./

CMD ["python", "-u", "./probe.py"]
