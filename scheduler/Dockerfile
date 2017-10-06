FROM python:3.6.2-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

ENTRYPOINT ["python3", "-u", "./scheduler.py"]
