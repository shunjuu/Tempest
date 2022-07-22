#!/bin/bash

# For hardware acceleration on Raspberry Pi 4+ devices, add:
# " --device /dev/video11 "
# to provide access to the encoder.

docker run -d \
        --name 'izumi-v6-tempest-alpha' \
        --restart unless-stopped \
        -l 'traefik.enable=false' \
        -v "$(pwd)/config/:/izumi/config" \
        --log-driver json-file \
        --log-opt max-size=10m \
        izumi-v6-tempest

docker logs -f "izumi-v6-tempest-alpha"