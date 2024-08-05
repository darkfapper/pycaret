FROM python:3.13.0b4-slim

WORKDIR /app

ADD . /app

RUN apt-get update && apt-get install -y libgomp1

RUN pip install --trusted-host pypi.python.org -r requirements.txt

CMD pytest