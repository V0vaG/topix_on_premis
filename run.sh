#!/bin/bash

source .env

ARCH=$(dpkg --print-architecture)
VERSION='1.0.2'

echo "arch: $ARCH"
echo "version: $VERSION "

docker_install(){
    # Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    #install docker-compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo systemctl restart docker
}

docker_build(){
    docker build --build-arg VERSION=$VERSION  -t vova0911/topix:${ARCH}_latest ./app
    docker build  -t vova0911/nginx:${ARCH}_latest ./nginx
    docker tag vova0911/topix:${ARCH}_latest vova0911/topix:${ARCH}_${VERSION}
}

docker_push(){
    echo "Logging into Docker Hub..."
#    read -p "Enter dockerhub user: " DOCKER_USERNAME
#    read -p "Enter dockerhub pass: " DOCKER_PASSWORD
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    if [ $? -ne 0 ]; then
        echo "Docker login failed. Exiting..."
        exit 1
    fi
    docker push vova0911/topix:${ARCH}_${VERSION}
    docker push vova0911/topix:${ARCH}_latest
    docker push vova0911/nginx:${ARCH}_latest
}

docker_cd(){
    docker-compose down

    echo "services:
    app:
        restart: always
        image: vova0911/topix:${ARCH}_latest
        command: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
        volumes:
            - /home/vova/script_files/topix:/root/script_files/topix
    nginx:
        container_name: nginx
        restart: always
        image: vova0911/nginx:${ARCH}_latest
        depends_on:
            - app
        ports:
            - "85:80"
    " > ./docker-compose_d.yml

    docker-compose -f ./docker-compose_d.yml up -d --build --scale app=2
}

# docker_install 

docker_build

docker_push

docker_cd
