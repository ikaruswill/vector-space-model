from nltk.tokenize import word_tokenize, sent_tokenize
import getopt
import sys
import os
import io

def build_dict(docs):
	dictionary = set()
	for doc_id, doc in docs.items():
		dictionary.update(doc)

	return dictionary

def populate_postings():
	pass

def load_data(dir_doc):
	docs = {}
	for dirpath, dirnames, filenames in os.walk(dir_doc):
		for name in filenames:
			file = os.path.join(dirpath, name)
			with io.open(file, 'r+') as f:
				docs[name] = f.read()

	return docs

def preprocess(docs):
	processed_docs = {}
	for doc_id, doc in docs.items():
		processed_docs[doc_id] = word_tokenize(doc)

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
