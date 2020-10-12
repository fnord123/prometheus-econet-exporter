FROM python:3

ENV CODE_DEST /opt/econet-exporter
WORKDIR ${CODE_DEST}

COPY econet-exporter.py ${CODE_DEST}

RUN pip install pyeconet prometheus_client envargparse

EXPOSE 8000

CMD [ "python", "./econet-exporter.py" ]
