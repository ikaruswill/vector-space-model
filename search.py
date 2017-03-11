import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize
from collections import Counter
import math
import string
import operator
import heapq
from pprint import pprint

dictionary = {}
postings_file = None
postings_sizes = []
starting_byte_offset = 0
all_doc_ids = []

def usage():
	print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -l lengths-file -o output-file-of-results")

def getPosting(index_of_term):
	# calculate byte offset
	posting_offset = 0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1]
	byte_offset = starting_byte_offset + posting_offset
	postings_file.seek(byte_offset, 0)
	posting = pickle.load(postings_file)
	return posting

def preprocess_query(query):
	stemmer = PorterStemmer()
	punctuations = set(string.punctuation)
	return Counter([stemmer.stem(token) for token in word_tokenize(query.lower()) if token not in punctuations])

def handleQuery(query):
	query = preprocess_query(query)
	scores = {} # To be replaced by heapq
	query_weights = []
	for term, query_tf in query.items():
		if term in dictionary:
			dict_entry = dictionary.get(term)
			postings_entry = getPosting(dict_entry['index'])
			idf = math.log10(len(lengths) / dict_entry['doc_freq'])
			query_tf_weight = 1 + math.log10(query_tf)
			for doc_id, doc_tf in postings_entry:
				doc_tf_weight = 1 + math.log10(doc_tf)
				if doc_id not in scores:
					scores[doc_id] = 0
				scores[doc_id] += doc_tf_weight * query_tf_weight * idf
			query_weights.append(query_tf_weight * idf)

	query_l2_norm = math.sqrt(sum([math.pow(1 + math.log10(query_weight), 2) for query_weight in query_weights]))
	for doc_id, score in scores.items():
		scores[doc_id] /= lengths[doc_id] * query_l2_norm

	#heapq by default is min heap, so * -1 to all score value
	scores_heap = [(-score, doc_id) for doc_id, score in scores.items()]
	heapq.heapify(scores_heap)

	if len(scores_heap) >= 10:
		return [heapq.heappop(scores_heap)[1] for i in range(10)]
	else:
		return [heapq.heappop(scores_heap)[1] for i in range(len(scores_heap))]

if __name__ == '__main__':
	dict_path = postings_path = query_path = output_path = lengths_path = None
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:l:')
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
		elif o == '-l':
			lengths_path = a
		else:
			assert False, "unhandled option"
	if dict_path == None or postings_path == None or query_path == None or output_path == None or lengths_path == None:
		usage()
		sys.exit(2)

	with open(dict_path, 'rb') as f:
		dictionary = pickle.load(f)

	with open(lengths_path, 'rb') as f:
		lengths = pickle.load(f)

	# load postings object sizes to calculate seek offset from current position of file
	postings_file = open(postings_path, 'rb')
	postings_sizes = pickle.load(postings_file)
	starting_byte_offset = postings_file.tell()

	output_file = open(output_path, 'w')
	with open(query_path, 'r') as f:
		for line in f:
			line = line.strip()
			if line != '':
				result = handleQuery(line)
				output = ' '.join(result)
				print('OUTPUT', output)
				output_file.write(output + '\n')
	output_file.close()
	postings_file.close()
