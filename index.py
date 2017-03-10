from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from collections import Counter
import getopt
import sys
import os
import io
import string
import pickle
import math
import operator

# Dictionary is a dictionary of {term: {index: i, doc_freq: n}}
# Postings is a dictionary of {term:{interval: x, doc_ids: list(doc_ids)}}

# takes in a dict of doc_id: Counter({term: freq}) items
# returns a dict of {term: term_dict}; term_dict is a dict of {index:i}
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
# returns a dict of term: posting dict objects
def init_postings(dictionary):
	postings = {}
	for term in dictionary:
		postings[term] = {}
		postings[term]['interval'] = 0
		postings[term]['doc_ids'] = []

	return postings

# takes in dict of doc_id: Counter({term: freq})
# takes in initialized postings dict of term: posting_dict
# returns dict of postings term: posting_dict; posting_dict is a dict {'interval': x, 'doc_ids': [(doc_ids, freq)]}
def populate_postings_and_skip(docs, postings):
	for doc_id, doc in sorted(docs.items(), key=lambda x:int(operator.itemgetter(0)(x))):
		for term, freq in doc.items():
			postings[term]['doc_ids'].append((doc_id, freq))

	for term, posting in postings.items():
		posting_len = len(postings[term]['doc_ids'])
		postings[term]['interval'] = math.floor((posting_len - 1) / math.floor(math.sqrt(posting_len)))

def populate_doc_freq(dictionary, postings):
	for term, term_dict in dictionary.items():
		term_dict['doc_freq'] = len(postings[term]['doc_ids'])

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

def save_object(object, path):
	with io.open(path, 'wb') as f:
		pickle.dump(object, f)


# takes in dict of term: posting_dict. posting_dict is a dict {'interval': x, 'doc_ids': [(doc_ids, freq)]}
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

	with io.open(postings_path, 'wb') as f:
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

# takes in dict of doc_id: [tokens]
# returns a dict of doc_id: length
def build_and_populate_lengths(docs):
	lengths = {}
	for doc_id, doc in docs.items():
		lengths[doc_id] = len(doc)
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
	lengths = build_and_populate_lengths(docs)
	docs = count_terms(docs)
	dictionary = build_dict(docs)
	postings = init_postings(dictionary)
	populate_postings_and_skip(docs, postings)
	populate_doc_freq(dictionary, postings)
	# skip_pointers = build_skip_pointers(postings)

	save_object(dictionary, dict_path)
	save_object(lengths, lengths_path)
	save_postings(postings)
