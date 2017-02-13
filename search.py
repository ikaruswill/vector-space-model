from nltk.stem.porter import PorterStemmer
import io
import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer

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

	for i in range(100):
		print(dictionary[i])

	# TODO: Implement seeking and reading don't read entirely

	# load postings object sizes to calculate seek offset from current position of file
	postings_file = io.open(postings_path, 'rb')
	postings_sizes = pickle.load(postings_file)
	starting_byte_offset = postings_file.tell()

	index_of_term = dictionary.index("bill")
	posting_offset = 0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1]

	print(pickle.load(postings_file))
	print(pickle.load(postings_file))
	postings_file.seek(starting_byte_offset + posting_offset, 0)
	print(pickle.load(postings_file))
	postings_file.seek(starting_byte_offset + posting_offset, 0)
	print(pickle.load(postings_file))

	with io.open(query_path, 'r') as f:
		# remove \n while readlines
		queries = [line[:-1] for line in f.readlines()]

	stemmer = PorterStemmer()

	for query in queries:
		print('***QUERY RESULT***')
		# encode to non-unicode
		stem = stemmer.stem(query.encode('ascii'))
		index_of_term = dictionary.index(stem)
		print(index_of_term)

		# skip if not found
		if index_of_term < 0:
			print(stem, 'not in dictionary')
			continue

		# calculate byte offset
		print(0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1])
		posting_offset = 0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1]
		byte_offset = starting_byte_offset + posting_offset
		print(byte_offset)
		postings_file.seek(byte_offset, 0)
		print(pickle.load(postings_file))

	postings_file.close()

	for i in range(3):
		print(random.choice(list(dictionary)))

	for i in range(3):
		term, ids = random.choice(list(postings.items()))
		while len(ids) < 4:
			term, ids = random.choice(list(postings.items()))
		print(term, ' ', ids, ' P: ', skip_pointers[term])