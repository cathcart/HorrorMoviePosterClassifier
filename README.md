# HorrorMoviePosterClassifier
### Background
Throughout the history of cinema movie posters have been used capture and sell the mood of a film. Whether it's an action-adventure, romantic-comedy or sci-fi horror movie genres have developed their own visual language to communicate to audiences. This project is my attempt to see if, via simple machine learning, computers can tap into this language. 
### Method
From a list of movies containing roughly equal numbers of horror and non-horror movies we download the movie details, such as which genres it belongs to, and poster images from [RottenTomatoes](http://developer.rottentomatoes.com/). Using [k-medoids](https://en.wikipedia.org/wiki/K-medoids) clustering we group the image pixels via colour value and calculate the fraction of the total number of pixels contained in each cluster. This gives us a reasonable idea of the colours used in each poster as well as their relative importance. Is the poster mainly black with white highlights or white with black text? 

To classify an unknown movie poster we extract these colour-fraction vectors using k-medoids before finding similar colour combinations from our database using the [K-nearest neighbors algorithm](https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm). This classifies if a poster is for a horror movie or not based on whether the majority of its k nearest neighbours are also horror movies.
###Additional details
Once downloaded the details for each movie along with our calculated colour-fraction vectors are saved in a redis database. This is to speed up repeat calculations and minimise the number of API calls to RottenTomatoes. Posters are also saved to the hard-disk so that in the event the user wishes to change the number of colour-fraction vectors used to approximate each poster no additional downloads are necessary. 
###Running
1. Setup the database first create a list of movie names. 
```
movie_list = ["The Ring", "Poltergeist", "The Exorcist", "Forrest Gump", "The Sound of Music", "Casablanca"]
```
   Larger lists will give more accurate results. An easy way to get large lists is to search for [imdb user lists](https://www.google.ie/search?q=g+horror+site%3Aimdb.com%2Flists&oq=g+horror+site%3Aimdb.com%2Flists&aqs=chrome..69i57j69i64l2.14941j0j1&sourceid=chrome&es_sm=91&ie=UTF-8#q=horror+site:imdb.com%2Flists) and parse the resulting RSS feeds to get a list of movie names. 

2. The database can then be initialised. 
```
d = Database(movie_list)
```
This will work itself though the list searching first for results on the redis server given before querying RottenTomatoes.

3. Suitable parameters, the number of clusters and nearest neighbours, are estimated and the database is trained searching for movies with the keyword `horror`.
```
d.cross_validation("horror")
```
4. An estimate of the accuracy of the database can be obtained using.
```
d.test()
```
This also prints the [confusion matrix](https://en.wikipedia.org/wiki/Confusion_matrix).
5. Individual movies can be tested with a simple get call to the database.
```
d["Gladiator"]
d["Titanic"]
d["The girl with the perl earring"]
```
### Dependencies
*redis
*PIL
*numpy
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

