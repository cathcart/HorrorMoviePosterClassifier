# HorrorMoviePosterClassifier
kNN classifier for movie horror posters.
### Dependencies
A redis server
PIL
numpy
### Building
A Docker image for the project can be built using the following Dockfile:
```
FROM        ubuntu:14.04
RUN         apt-get update -yq && apt-get install -yq vim && apt-get install -yq python && apt-get install -yq python-pip
RUN         apt-get install -yq python-dev
RUN         apt-get install -yq libjpeg-dev zlib1g-dev
RUN         apt-get -yq install libblas-dev libatlas-dev liblapack-dev gfortran
RUN         pip install redis
RUN         pip install pillow
RUN         pip install numpy
``` 
This is then build and run with the commands:
```
docker build -t MovieClassifier-Image .
docker run -v $PWD:/work-dir --name MovieClassifier-Image --link redis:db -i -t MovieClassifier
```
You can then `cd work-dir` to get into the mounted volume in the container and run the classifier with `python main.py`. The inital run will be slow as the project has to download and calculate the colours of the posters within the database.

###Building a redis server with docker
A suitable redis server for this project can be built with:
```
FROM        ubuntu:14.04
RUN         apt-get update && apt-get install -y redis-server
EXPOSE      6379
ENTRYPOINT  ["/usr/bin/redis-server"]
```
It can be built and run with:
```
docker build -t <your username>/redis .
docker run --name redis -d <your username>/redis
```

