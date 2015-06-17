import redis
from PIL import Image
import numpy as np
import math
import os
import urllib
import json
import requests
from StringIO import StringIO
import random
from xml.etree import ElementTree as etree
import time

#redis host added through enviormental variables
redis_host = os.environ['DB_PORT_6379_TCP_ADDR']
#rotten tomatoes api key held in file 'api.key'
api_key = file("api.key").read().strip("\n")

class Movie(object):
	def __init__(self, name, replace=False):
		if r.exists(name) and not replace:
			#load
			#print "loading", name.encode('utf-8')
			self.__load(r.get(name))
		else:
			#create movie oject using name
			#print "downloading", name.encode('utf-8')
			self.id = self.__find_id(name)
			if self.id != None:
				self.__download(name)
				self.__checkget_poster(replace)
				img = Image.open("./posters/"+urllib.quote_plus(self.title)+".jpg")
				color_data = map(lambda x: np.array([y/255.0 for y in x]), list(img.getdata()))
				self.average_colors = self.kmedoids(color_data,5, fractions=True)
			self.__save(name)

	def __save(self, name):
		r.set(name, json.dumps(self.__dict__))

	def __load(self, data):
		j = json.loads(data)
		self.id = j["id"]
		if self.id != None:
			self.title = j["title"]
			self.genres = j["genres"]
			self.poster_url = j["poster_url"]
			self.average_colors = map(np.array,j["average_colors"])

	def __find_id(self, name):
		s = "http://api.rottentomatoes.com/api/public/v1.0/movies.json"
		response = requests.get(s,params={'apikey':api_key, 'q':name})
		response.url
		self.__rt_error_catch(response)
		j = response.json()
		try:
			self.id = j['movies'][0]['id']
			self.title = j['movies'][0]['title']
			return j['movies'][0]['id']
		except IndexError:
			print "\tNo results found for", name.encode('utf-8')
			return None

	def __download(self, name):
		s = "http://api.rottentomatoes.com/api/public/v1.0/movies/{id}.json".format(**{"id":self.id})
		response = requests.get(s,params={'apikey':api_key})
		self.__rt_error_catch(response)
		j = response.json()
		self.title = j["title"]
		self.genres = map(lambda x: x.lower(),j["genres"])
		self.poster_url = j["posters"]["thumbnail"]
		self.average_colors = None

	def __checkget_poster(self, replace):
		if not os.path.exists("./posters"):
			os.mkdir("./posters")
		if not os.path.exists("./posters/"+urllib.quote_plus(self.title)) or replace:
			response = requests.get(self.poster_url)
			self.__rt_error_catch(response)
			img = Image.open(StringIO(response.content))
			img.convert('RGB').save("./posters/"+urllib.quote_plus(self.title)+".jpg","JPEG")

	def compute_squared_EDM(self,X):
		#calculate squared eucledian distance matrix
		#get dimensions of X
		n,m = X.shape
	
		#compute the Gram matrix
		G = np.dot(X,X.T)	
		#compute matrix H
		H = np.tile(np.diag(G),(n,1))
		return H + H.T - 2*G

	def get_unique_colors(self, data):
		uniques = {}
		for color in data:
			c = tuple(color)
			if c not in uniques.keys():
				uniques[c] = 1
			else:
				uniques[c] += 1
		return uniques

	def kmedoids(self, data_list, k, tmax=100, fractions=False):
		#remove duplicates from data
		uniques = self.get_unique_colors(data_list)
		data = np.matrix(uniques.keys())
		#pre-calculate squared euclidian distance matrix
		D = self.compute_squared_EDM(data)
		#get dimensions of D
		m,n = D.shape
		#randomly initialise an array of medoid indices
		M = np.sort(np.random.choice(n,k, replace=False))
		#create copy of M
		Mnew = np.copy(M)
		#make dict for clusters
		C = {}
	
		for t in xrange(tmax):
			#determine clusers
			J = np.argmin(D[:,M],axis=1)
			#J is a list of which clusters each data point belong to
			for kappa in range(k):
				C[kappa] = np.where(J==kappa)[0]

			#update cluster medoids
			for kappa in range(k):
				J2 = np.mean(D[np.ix_(np.array(C[kappa])[0],np.array(C[kappa])[0])], axis=0)
				j = np.argmin(J2)
				Mnew[kappa] = C[kappa][0,j]
			np.sort(Mnew)

			#check for convergence
			if np.array_equal(M,Mnew):
				break
			M = np.copy(Mnew)
		else:
			#final upate of cluster memberships
			J = np.argmin(D[:,M],axis=1)
			for kappa in range(k):
				C[kappa] = np.where(J==kappa)[0]

		average_colors = data[M].tolist() # return these colors
		if fractions:
			cluster_counts = [sum([uniques[tuple(data[j].tolist()[0])] for j in C[i].tolist()[0]]) for i in range(k)]
			return sorted([average_colors[i]+[cluster_counts[i]/float(sum(cluster_counts))] for i in range(k)], key=lambda x: x[-1])
		else:
			return sorted(average_colors, key=lambda x: x[-1], reverse=True)

	def __rt_error_catch(self, response):
		if response.status_code != 200:
			raise NameError("Rotten Tomatoes did not respond correctly ", response.status_code)

class Database(Movie):
	def __init__(self, movies, replace=False):
		self.movies = filter(lambda x: x.id!=None,[Movie(m,replace) for m in movies])
		#split the movies into train (80%), cross-validation (10%) and test (10%)
		self.train_set = [random.choice(self.movies) for x in range(int(math.floor(len(self.movies)*0.8)))]
		remaining_movies = [m for m in self.movies if m not in self.train_set]
		self.cross_validation_set = [random.choice(self.movies) for x in range(int(math.floor(len(remaining_movies)*0.5)))]
		self.test_set = [m for m in remaining_movies if m not in self.cross_validation_set]
		self.trained = False

	def train(self, key, n):
		match_colors = []
		antimatch_colors = []
		self.key = key
		for m in self.train_set:
			if key in m.genres:
				match_colors += [m.average_colors[-1]]
			else:
				antimatch_colors += [m.average_colors[-1]]

		match = super(Database,self).kmedoids(match_colors, n)
		antimatch = super(Database,self).kmedoids(antimatch_colors, n)

		self.match = match
		self.antimatch = antimatch
		self.trained = True

	def cross_validation(self, key):
		self.key = key
		i = 15
		k = 9
		m = (0,0,0)
		for i in range(1,11,1):
			for k in range(1,11,1):
				self.train(key,i)
				t = 100*self.__internal_test(self.cross_validation_set,k)[0]
				if t > m[0]:
					m = (t,i,k)
				#print t,"\t",
			#print
		#print "max", m
		self.train(key,m[-2])
		self.k = m[-1]
	
	def __getitem__(self, name):
		m = Movie(name, replace=False)
		if self.trained == False:
			raise NameError("Train database before trying to evaluate movies with it")
		return self.__knn(self.k, m)

	def __knn(self, k, movie):
		all_movies = self.match + self.antimatch
		s = 0.0
		for c in [movie.average_colors[-1]]:
			distances = [np.array(c).dot(np.array(x)) for x in all_movies]
			nearestk = sorted(distances, reverse=True)[:k]
			idxs = [distances.index(x) for x in nearestk]
			for m in [all_movies[i] for i in idxs]:
				if m in self.match:
					s += 1.0/k
				elif m in self.antimatch:
					s += 0.0/k

		return s > 0.5

	def __internal_test(self, test_set, k=None):
		if k == None:
			k = self.k
		tp = 0.0
		tn = 0.0
		fp = 0.0
		fn = 0.0
		for m in self.test_set:
			actual =  unicode(self.key) in m.genres
			result = self.__knn(k,m)
			if actual == result == True:
				tp += 1.0
			elif actual == result == False:
				tn += 1.0
			elif actual != result:
				if actual == True:
					fn += 1.0
				elif actual == False:
					fp += 1.0
		return (tp+tn)/(tp+tn+fn+fp), np.matrix([[tp,fn],[fp,tn]])

	def test(self):
		fraction, confusion_matrix = self.__internal_test(self.test_set) 
		print "%d %s movies in training set out of a total of %d"%(len([x for x in self.train_set if self.key in x.genres]),self.key, len(self.train_set))
		print "Percentage correct: %0.2f"% (100*fraction)
		print "Confusion matrix"
		print confusion_matrix
		print np.matrix([["tp","fn"],["fp","tn"]])

	def delete(self, movies):
		for name in movies:
			r.delete(name)

def get_rss(url):
	print "getting ", url
	time.sleep(1)
	response = requests.get(url)
	root = etree.fromstring(response.text)
	return map(lambda x:x.text,root.findall('channel/item/title'))

if __name__=="__main__":
	horror_lista = "http://rss.imdb.com/list/ls057964714/"	
	horror_listb = "http://rss.imdb.com/list/ls058838235/"
	horror_list = "http://rss.imdb.com/list/ls057964714/"	
	top_list = "http://rss.imdb.com/list/ls055592025/"
	empire_list = "http://rss.imdb.com/list/ls003073623/"
#	u = "http://rss.imdb.com/list/ls072031365"
	#print get_rss(u)
	r = redis.StrictRedis(host=redis_host,port=6379,db=0)
	d = Database(get_rss(horror_lista)+get_rss(horror_listb)+get_rss(empire_list), replace=False)
	d.cross_validation("horror")
	d.test()
