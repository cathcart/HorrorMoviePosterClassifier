# HorrorMoviePosterClassifier
### Background
Throughout the history of cinema movie posters have been used capture and sell the mood of a film. Whether it's an action-adventure, romantic-comedy or sci-fi horror movie genres have developed their own visual language to communicate to audiences. This project is my attempt to see if, via simple machine learning, computers can tap into this language. 
### Method
From a list of movies containing roughly equal numbers of horror and non-horror movies we download the movie details, such as which genres it belongs to, and poster images from [RottenTomatoes](http://developer.rottentomatoes.com/). Using [k-medoids](https://en.wikipedia.org/wiki/K-medoids) clustering we group the image pixels via colour value and calculate the fraction of the total number of pixels contained in each cluster. This gives us a reasonable idea of the colours used in each poster as well as their relative importance. Is the poster mainly black with white highlights or white with black text? To classify an unknown movie poster we extract these colour-fraction vectors using k-medoids before finding similar colour combinations from our database using the [K-nearest neighbors algorithm](https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm). This classifies if a poster is for a horror movie or not based on whether the majority of its k nearest neighbours are also horror movies.
###Additional details
Once downloaded the details for each movie along with our calculated colour-fraction vectors are saved in a redis database. This is to speed up repeat calculations and minimise the number of API calls to RottenTomatoes. Posters are also saved to the hard-disk so that in the event the user wishes to change the number of colour-fraction vectors used to approximate each poster no additional downloads are necessary. 
### Dependencies
redis
PIL
numpy
### Building
A Docker image for the project can be built using the following Dockerfile:
```
FROM        ubuntu:14.04
RUN         apt-get update -yq
RUN         apt-get install -yq python python-pip
RUN         apt-get install -yq python-dev
RUN         apt-get install -yq libjpeg-dev zlib1g-dev
RUN         apt-get -yq install libblas-dev libatlas-dev liblapack-dev gfortran
RUN         pip install redis
RUN         pip install pillow
RUN         pip install numpy
``` 
This is then built and run with the commands:
```
docker build -t MovieClassifier-Image .
docker run -v $PWD:/work-dir --name MovieClassifier-Image --link redis:db -i -t MovieClassifier
```
We can then `cd work-dir` to get into the mounted volume in the container and run the classifier with `python main.py`. The initial run will be slow as the project has to download and calculate the colours for all the posters within the database.

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

