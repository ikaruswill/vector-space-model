from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.porter import PorterStemmer
import getopt
import sys
import os
import io
import string
import pickle

def build_dict(docs):
	dictionary = set()
	for doc_id, doc in docs.items():
		dictionary.update(doc)

	dictionary = list(dictionary)
	dictionary.sort()

	return dictionary

def build_postings(dictionary):
	postings = {}
	for term in dictionary:
		postings[term] = []

	return postings

def populate_postings(docs, postings):
	for doc_id, doc in sorted(docs.items(), key=lambda x:int(operator.itemgetter(0)(x))):
		for term in set(doc):
			postings[term].append(doc_id)

def load_data(dir_doc):
	docs = {}
	for dirpath, dirnames, filenames in os.walk(dir_doc):
		for name in filenames:
			file = os.path.join(dirpath, name)
			with io.open(file, 'r') as f:
				docs[name] = f.read()

	return docs

def preprocess(docs):
	stemmer = PorterStemmer()
	punctuations = set(string.punctuation)
	processed_docs = {}
	for doc_id, doc in docs.items():
		processed_docs[doc_id] = set([stemmer.stem(token) for token in word_tokenize(doc.lower())])
		processed_docs[doc_id].difference_update(punctuations)

	return processed_docs

def usage():
	print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

if __name__ == '__main__':
	dir_doc = dict_file = postings_file = None
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
	except getopt.GetoptError as err:
		usage()
		sys.exit(2)
	for o, a in opts:
		if o == '-i':
			dir_doc = a
		elif o == '-d':
			dict_file = a
		elif o == '-p':
			postings_file = a
		else:
			assert False, "unhandled option"
	if dir_doc == None or dict_file == None or postings_file == None:
		usage()
		sys.exit(2)

	docs = load_data(dir_doc)
	docs = preprocess(docs)
	dictionary = build_dict(docs)
	postings = build_postings(dictionary)
	populate_postings(docs, postings)


	with io.open(dict_file, 'wb') as f:
		pickle.dump(dictionary, f)

	with io.open(postings_file, 'wb') as f:
		pickle.dump(postings, f)
