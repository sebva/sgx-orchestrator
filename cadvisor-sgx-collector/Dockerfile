# This image represents a potential SGX application
FROM python:3.6.1-alpine3.6

COPY collector_config.json /var/cadvisor/collector_config.json
COPY collector.py /opt/collector.py

LABEL io.cadvisor.metric.sgx="/var/cadvisor/collector_config.json"

EXPOSE 4567
CMD ["python3", "/opt/collector.py"]
