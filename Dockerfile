FROM python:3.8-slim

LABEL maintainer="Kyrielight"

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python depdencies
RUN apt-get update -y && \
    apt-get install -y git ffmpeg

# Install rclone
RUN apt-get install -y unzip curl && \
    curl 'https://rclone.org/install.sh' | bash


COPY requirements.txt /opt/requirements.txt
RUN pip3 install -r /opt/requirements.txt && rm /opt/requirements.txt

COPY *.py /izumi/
COPY assets/*.ttf /opt/fonts/

WORKDIR /izumi
ENTRYPOINT ["python3", "/izumi/tempest.py"]