# This image is the "collector" that will fetch information from the isgx driver, and make it available by HTTP to
# cAdvisor. There should be one instance per SGX-enabled node in a Swarm.
FROM python:3.6.1-alpine3.6

COPY collector_config.json /var/cadvisor/collector_config.json
COPY collector.py /opt/collector.py

LABEL io.cadvisor.metric.sgx="/var/cadvisor/collector_config.json"

STOPSIGNAL SIGINT
EXPOSE 4567
CMD ["python3", "/opt/collector.py"]
