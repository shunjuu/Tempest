FROM python:3.8-slim

LABEL maintainer="Kyrielight"

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python depdencies
RUN apt-get update -y && \
    apt-get install -y wget git xz-utils unzip curl

# Install rclone
RUN curl 'https://rclone.org/install.sh' | bash

# --- DISABLED as the user should provide their own ffmpeg build due to system limitations. --- #
# --- Eventually we should write a script to handle this. --- #
# Install ffmpeg
# COPY install_ffmpeg.sh /opt/install_ffmpeg.sh
# RUN /opt/install_ffmpeg.sh && rm /opt/install_ffmpeg.sh

COPY requirements.txt /opt/requirements.txt
RUN pip3 install -r /opt/requirements.txt && rm /opt/requirements.txt

COPY *.py /izumi/
COPY assets/fonts/*.ttf /opt/fonts/
COPY assets/bin/* /usr/bin/

WORKDIR /izumi
ENTRYPOINT ["python3", "/izumi/tempest.py"]