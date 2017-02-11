import io
import getopt
import sys
import pickle

def usage():
	print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

if __name__ == '__main__':
	dict_file = postings_file = query_file = output_file = None
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
	except getopt.GetoptError as err:
		usage()
		sys.exit(2)
	for o, a in opts:
		if o == '-d':
			dict_file = a
		elif o == '-p':
			postings_file = a
		elif o == '-q':
			query_file = a
		elif o == '-o':
			output_file = a
		else:
			assert False, "unhandled option"
	if dict_file == None or postings_file == None or query_file == None or output_file == None:
		usage()
		sys.exit(2)

	with io.open(dict_file, 'rb') as f:
		dictionary = pickle.load(f)
	
	# TODO: Implement seeking and reading don't read entirely
	with io.open(postings_file, 'rb') as f:
		postings = pickle.load(f)

	with io.open(query_file, 'r') as f:
		queries = f.readlines()

	stemmer = PorterStemmer()

	for query in queries:
		print('QUERY RESULT')
		print(postings[stemmer.stem(query)])
