FROM docker.io/python:3.15-alpine3.24

RUN pip install pykmip

COPY kmip.conf /etc/pykmip/pykmip.conf

EXPOSE 5696

#USER 1000

CMD ["pykmip-server", "--config", "/etc/pykmip/pykmip.conf"]