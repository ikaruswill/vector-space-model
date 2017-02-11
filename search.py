import io
import getopt
import sys
import pickle

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
	with io.open(postings_file, 'rb') as f:
		postings = pickle.load(f)

	with io.open(query_path, 'r') as f:
		queries = f.readlines()

	stemmer = PorterStemmer()

	for query in queries:
		print('QUERY RESULT')
		print(postings[stemmer.stem(query)])
