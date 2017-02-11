from nltk.stem.porter import PorterStemmer
import io
import getopt
import sys
import pickle

import random

def usage():
	print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

if __name__ == '__main__':
	dict_path = postings_path = query_path = output_path = None
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
	except getopt.GetoptError as err:
		usage()
		sys.exit(2)
	for o, a in opts:
		if o == '-d':
			dict_path = a
		elif o == '-p':
			postings_path = a
		elif o == '-q':
			query_path = a
		elif o == '-o':
			output_path = a
		else:
			assert False, "unhandled option"
	if dict_path == None or postings_path == None or query_path == None or output_path == None:
		usage()
		sys.exit(2)

	with io.open(dict_path, 'rb') as f:
		dictionary = pickle.load(f)

	# TODO: Implement seeking and reading don't read entirely
	
	# load postings object sizes to calculate seek offset from current position of file
	postings_file = io.open(postings_path, 'rb')
	postings_sizes = pickle.load(postings_file)

	with io.open(query_path, 'r') as f:
		queries = f.readlines()

	postings_file.close()

	stemmer = PorterStemmer()

	for query in queries:
		print('QUERY RESULT')
		print(postings[stemmer.stem(query)])

	for i in range(3):
		print(random.choice(list(dictionary)))

	for i in range(3):
		term, ids = random.choice(list(postings.items()))
		while len(ids) < 4:
			term, ids = random.choice(list(postings.items()))
		print(term, ' ', ids, ' P: ', skip_pointers[term])