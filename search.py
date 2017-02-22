import io
import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer
from pprint import pprint

operator_precedence_table = {
	'NOT': 3,
	'AND': 2,
	'OR' : 1,
}

dictionary = ''
postings_file = ''
postings_sizes = ''
starting_byte_offset = ''

def usage():
	print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

def getPrecedence(operator):
	if operator_precedence_table.get(operator) is None:
		return 0
	else:
		return operator_precedence_table[operator]

def getPrevPrecedence(operator_stack):
	return getPrecedence(operator_stack[0]) if len(operator_stack) > 0 else 0

def shuntingYard(tokens_and_operators):
	available_operators = operator_precedence_table.keys()
	operator_stack = []
	output = []
	for token_or_operator in tokens_and_operators:
		if token_or_operator == ')':
			while True:
				if len(operator_stack) > 0 and operator_stack[0] == '(':
					operator_stack.pop(0)
					break
				output.append(operator_stack.pop(0))
		elif token_or_operator == '(':
			operator_stack.insert(0, token_or_operator)
		elif token_or_operator.upper() in available_operators:
			cur_precendence = getPrecedence(token_or_operator.upper())
			prev_precendence = getPrevPrecedence(operator_stack)

			if cur_precendence < prev_precendence:
				output.append(operator_stack.pop(0))
			operator_stack.insert(0, token_or_operator)
		else:
			output.append(getDictionaryEntry(token_or_operator))
	output.extend(operator_stack)

	pprint(output)
	return output

def getDictionaryEntry(term):
	stemmer = PorterStemmer()

	stem = stemmer.stem(term)
	return {} if dictionary.get(stem) is None else dictionary[stem]

def getDocIds(term):
	stemmer = PorterStemmer()

	stem = stemmer.stem(term)
	index_of_term = -1 if dictionary.get(stem) is None else dictionary[stem]['index']

	# skip if not found
	if index_of_term < 0:
		print(stem, 'not in dictionary')
		return []

	# calculate byte offset
	posting_offset = 0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1]
	byte_offset = starting_byte_offset + posting_offset
	postings_file.seek(byte_offset, 0)
	posting = pickle.load(postings_file)
	return posting.get('doc_ids')


def handleQuery(query):
	print('query: ', query)
	processed_query = shuntingYard(query.split(' '))

	for idx, item in enumerate(processed_query):
		if item == 'NOT':
			continue
		elif item == 'AND':
			consecutive_and = 1
			offset = 1
			while idx + offset < len(processed_query) and processed_query[idx + offset] == 'AND':
				consecutive_and += 1
				offset += 1
			print('consecutive_and', consecutive_and)
		elif item == 'OR':
			continue



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

	# load postings object sizes to calculate seek offset from current position of file
	postings_file = io.open(postings_path, 'rb')
	postings_sizes = pickle.load(postings_file)
	starting_byte_offset = postings_file.tell()

	print('***QUERY RESULT***')

	with io.open(query_path, 'r') as f:
		query = f.readline()[:-1] #remove \n
		while query:
			handleQuery(query)
			query = f.readline()[:-1]

	postings_file.close()
