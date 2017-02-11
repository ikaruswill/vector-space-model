from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
import getopt
import sys
import os
import io
import string
import pickle
import math
import operator

# Dictionary is a sorted list of terms
# Postings is a dictionary of {term:{interval: x, doc_ids: list(doc_ids)}}

# takes in a dict of doc_id: doc items
# returns a sorted list of non-duplicated terms in collection
def build_dict(docs):
	dictionary = set()
	for doc_id, doc in docs.items():
		dictionary.update(doc)

	dictionary = list(dictionary)
	dictionary.sort()

	return dictionary

def build_postings(dictionary):
# takes in a list of terms
# returns a dict of term: posting dict objects
def build_postings(sorted_dict):
	postings = {}
	for term in dictionary:
		postings[term] = {}
		postings[term]['interval'] = 0
		postings[term]['doc_ids'] = []

	return postings

# def build_skip_pointers(postings):
# 	skip_pointers = {}
# 	for term, posting_list in postings.items():
# 		postings_len = len(posting_list)
# 		if postings_len > 3:
# 			pointer_count = math.floor(math.sqrt(postings_len))
# 			pointer_interval = math.floor(postings_len / pointer_count)
# 			pointers = []
# 			skip_pointers[term] = [i for i in range(pointer_interval - 1, postings_len, pointer_interval)]
# 		elif postings_len == 3:
# 			skip_pointers[term] = [2]
# 		else:
# 			skip_pointers[term] = []

# 	return skip_pointers

# takes in dict of doc_id:set(processed_doc) 
# takes in initialized postings dict of term: posting_dict
# returns dict of postings term: posting_dict; posting_dict is a dict {'interval': x, 'doc_ids': [doc_ids]}
def populate_skip_postings(docs, postings):
	for doc_id, doc in sorted(docs.items(), key=lambda x:int(operator.itemgetter(0)(x))):
		for term in set(doc):
			postings[term]['doc_ids'].append(doc_id)

	for term, posting in postings.items():
		posting_len = len(postings[term]['doc_ids'])
		postings[term]['interval'] = math.floor((posting_len - 1) / math.floor(math.sqrt(posting_len)))

# takes in directory of corpus
# returns dict of doc_id: string(doc)
def load_data(dir_doc):
	docs = {}
	for dirpath, dirnames, filenames in os.walk(dir_doc):
		for name in filenames:
			file = os.path.join(dirpath, name)
			with io.open(file, 'r') as f:
				docs[name] = f.read()

	return docs

# takes in dict of term: posting_dict. posting_dict is a dict {'interval': x, 'doc_ids': [doc_ids]}
# saves list of object sizes in bytes in sorted order of terms as first object, saves each posting_dict as separate, subsequent objects.
def save_postings(postings):
	sizes = []
	pickled_postings = []

	# Generate posting objects
	for term, posting in postings.items():
		pickled_posting = pickle.dumps(posting)
		sizes.append(len(pickled_posting))
		pickled_postings.append(pickled_posting)

	with io.open(postings_file, 'wb') as f:
		pickle.dump(sizes, f)
		for pickled_posting in pickled_postings:
			f.write(pickled_posting)

# takes in dict of doc_id: string(doc)
# returns tokenized, stemmed, punctuation-filtered dict of doc_id: set(preprocessed_tokens)
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
	populate_skip_postings(docs, postings)
	# skip_pointers = build_skip_pointers(postings)

	with io.open(dict_file, 'wb') as f:
		pickle.dump(dictionary, f)

	save_postings(postings)

