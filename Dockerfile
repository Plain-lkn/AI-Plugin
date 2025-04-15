FROM python:3.10.11-slim

COPY . /src
WORKDIR /src

RUN apt-get update && apt-get -y install libgl1-mesa-glx \
&& apt-get -y install libglib2.0-0
RUN pip install --upgrade pip && pip install -r requirements.txt