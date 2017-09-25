FROM python:3.6.2-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

CMD ["python", "-u", "./scheduler.py"]
