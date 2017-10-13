FROM debian:stretch-slim

RUN apt-get update && \
    apt-get install -yqq stress-ng && \
    rm -rf /var/cache/apt

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

