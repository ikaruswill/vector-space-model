import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import word_tokenize
import math
import string

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
	return [stemmer.stem(token) for token in word_tokenize(query.lower()) if token not in punctuations]

def handleQuery(query):
	query = preprocess_query(query)
	scores = {} # To be replaced by heapq
	for term in query:
		if term in dictionary:
			dict_entry = dictionary.get(stem)
			postings_entry = getPosting(dict_entry['index'])
			idf = math.log10(len(lengths) / dict_entry['doc_freq'])
			for doc_id, term_freq in postings_entry:
				tf = 1 + math.log10(term_freq)
				if doc_id not in scores:
					scores[doc_id] = 0
				scores[doc_id] += tf * idf

	pass # Return top 10






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
				try:
					result = handleQuery(line)
					output = ' '.join(result)
					# print('OUTPUT', output)
					output_file.write(output + '\n')
				except Exception as e:
					output_file.write('\n')
					print('****WARN***** EXCEPTION THROWN', e)
					continue

	output_file.close()
	postings_file.close()

	print('++ 3 Random items in dictionary ++')
	for i in range(3):
		print(random.choice(list(dictionary.items())))