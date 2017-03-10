from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from collections import Counter
import getopt
import sys
import os
import string
import pickle
import math
import operator

import random

# Dictionary is a dictionary of {term: {index: i, doc_freq: n}}
# Postings is a dictionary of {term:[(doc_id, freq), ...]}

# takes in a dict of doc_id: Counter({term: freq}) items
# returns a dict of {term: {index: i}}
def build_dict(docs):
	dictionary = set()
	for doc_id, doc in docs.items():
		dictionary.update(doc.keys())

	dictionary_ordered = list(dictionary)
	dictionary_ordered.sort()

	dictionary = {}
	for i, term in enumerate(dictionary_ordered):
		dictionary[term] = {'index': i}

	return dictionary

# takes in a list of terms
# returns a dict of term: []
def build_postings(dictionary):
	postings = {}
	for term in dictionary:
		postings[term] = []

	return postings

# takes in dict of doc_id: Counter({term: freq})
# takes in initialized postings dict of term: posting_dict
# returns dict of term: [(doc_id, freq), ...]
def populate_postings(docs, postings):
	for doc_id, doc in sorted(docs.items()):
		for term, freq in doc.items():
			postings[term].append((doc_id, freq))

def populate_doc_freq(dictionary, postings):
	for term, term_dict in dictionary.items():
		term_dict['doc_freq'] = len(postings[term])

# takes in directory of corpus
# returns dict of doc_id: string(doc)
def load_data(dir_doc):
	docs = {}
	for dirpath, dirnames, filenames in os.walk(dir_doc):
		for name in filenames:
			file = os.path.join(dirpath, name)
			with open(file, 'r') as f:
				docs[name] = f.read()

	return docs

def save_object(object, path):
	with open(path, 'wb') as f:
		pickle.dump(object, f)


# takes in dict of term: posting_dict. posting_dict is a dict {'interval': x, 'doc_ids': [(doc_id, freq), ...]}
# saves list of object sizes in bytes in sorted order of terms as first object, saves each posting_dict as separate, subsequent objects.
def save_postings(postings):
	sizes = []
	pickled_postings = []

	# Generate posting objects
	cumulative = 0
	for term, posting in sorted(postings.items()):
		pickled_posting = pickle.dumps(posting)
		cumulative += len(pickled_posting)
		sizes.append(cumulative)
		pickled_postings.append(pickled_posting)

	with open(postings_path, 'wb') as f:
		pickle.dump(sizes, f)
		for pickled_posting in pickled_postings:
			f.write(pickled_posting)

# takes in dict of doc_id: string(doc)
# returns tokenized, stemmed, punctuation-filtered dict of doc_id: [tokens]
def preprocess(docs):
	stemmer = PorterStemmer()
	punctuations = set(string.punctuation)
	processed_docs = {}
	for doc_id, doc in docs.items():
		# try to remove terms start and end with number
		# processed_docs[doc_id] = set([stemmer.stem(token) for token in word_tokenize(doc.lower()) if not token[0].isdigit() or not token[-1].isdigit()])
		processed_docs[doc_id] = [stemmer.stem(token) for token in word_tokenize(doc.lower()) if token not in punctuations]
	return processed_docs

# takes in dict of doc_id: [tokens]
# returns a dict of doc_id: Counter({term: freq}) items
def count_terms(docs):
	processed_docs = {}
	for doc_id, doc in docs.items():
		processed_docs[doc_id] = Counter(doc)
	return processed_docs

# takes in dict of doc_id: Counter({term: freq})
# returns a dict of doc_id: length
def build_and_populate_lengths(docs):
	lengths = {}
	for doc_id, doc in docs.items():
		sum_squares = 0
		for term, freq in doc.items():
			sum_squares += math.pow(1 + math.log10(freq), 2)
		lengths[doc_id] = math.sqrt(sum_squares)

	return lengths

def usage():
	print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file -l lengths-file")

if __name__ == '__main__':
	dir_doc = dict_path = postings_path = lengths_path = None
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:l:')
	except getopt.GetoptError as err:
		usage()
		sys.exit(2)
	for o, a in opts:
		if o == '-i':
			dir_doc = a
		elif o == '-d':
			dict_path = a
		elif o == '-p':
			postings_path = a
		elif o == '-l':
			lengths_path = a
		else:
			assert False, "unhandled option"
	if dir_doc == None or dict_path == None or postings_path == None or lengths_path == None:
		usage()
		sys.exit(2)

	docs = load_data(dir_doc)
	docs = preprocess(docs)
	docs = count_terms(docs)
	lengths = build_and_populate_lengths(docs)
	dictionary = build_dict(docs)
	postings = build_postings(dictionary)
	populate_postings(docs, postings)
	populate_doc_freq(dictionary, postings)

	save_object(dictionary, dict_path)
	save_object(lengths, lengths_path)
	save_postings(postings)

	print('++ 3 Random items in docs ++')
	for i in range(3):
		print(random.choice(list(docs.items())))

	print('++ 3 Random items in dictionary ++')
	for i in range(3):
		print(random.choice(list(dictionary.items())))

	print('++ 3 Random items in postings with len > 4, with doc_freq ++')
	for i in range(3):
		term, posting = random.choice(list(postings.items()))
		while len(posting) < 4:
			term, posting = random.choice(list(postings.items()))
		print(term, ' ', posting)
		print('doc_freq:', dictionary[term]['doc_freq'], 'actual:', len(posting))

	print('++ 3 Random items in lengths ++')
	for i in range(3):
		doc_id, length = random.choice(list(lengths.items()))
		print('{', doc_id, ':', length, '}')