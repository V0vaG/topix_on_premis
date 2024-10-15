#!/bin/bash

# sudo docker build ./app -t topix
# sudo docker compose up
sudo docker compose up -d --build --scale app=4

sudo docker run -it -p 5000:5000 topix
