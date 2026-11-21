FROM docker.io/python:3.15-alpine3.24

ENV KMIP_KEY_NAME=openbao-seal-key \
    KMIP_MAX_RETRIES=10 \
    KMIP_RETRY_DELAY=5

RUN pip install --no-cache-dir pykmip

COPY kmip.conf /etc/pykmip/pykmip.conf

COPY --chmod=755 get_key_id.py /usr/local/bin/get_key_id

EXPOSE 5696

CMD ["pykmip-server", "--config", "/etc/pykmip/pykmip.conf"]
