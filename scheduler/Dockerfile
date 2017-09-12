FROM python:3.6.2-alpine

WORKDIR /usr/src/app

RUN pip install --no-cache-dir kubernetes
COPY scheduler.py .

CMD ["python", "./scheduler.py"]
