import io
import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer
import math
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
			while cur_precendence < prev_precendence:
				output.append(operator_stack.pop(0))
				cur_precendence = getPrecedence(token_or_operator.upper())
				prev_precendence = getPrevPrecedence(operator_stack)
			operator_stack.insert(0, token_or_operator)
		else:
			output.append(getDictionaryEntry(token_or_operator))
			# output.append(token_or_operator)
	output.extend(operator_stack)

	print('SHUNTING YARD: ', output)
	return output

def getDictionaryEntry(term):
	stemmer = PorterStemmer()
	stem = stemmer.stem(term)
	return {'doc_freq': 0} if dictionary.get(stem) is None else dictionary[stem]

def getPosting(index_of_term):
	# calculate byte offset
	posting_offset = 0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1]
	byte_offset = starting_byte_offset + posting_offset
	postings_file.seek(byte_offset, 0)
	posting = pickle.load(postings_file)
	return posting

def getPostingFromDictEntry(dict_entry):
	if dict_entry.get('posting') is not None:
		return dict_entry['posting']
	elif dict_entry.get('index') is not None:
		return getPosting(dict_entry['index'])
	else:
		return { 'doc_ids': [] }

def findMatch(idx, pst, target_doc_id):
	has_skip = idx % (pst['interval'] + 1) == 0
	new_idx = min( idx + pst['interval'] + 1, len(pst['doc_ids']) - 1 ) if has_skip else idx + 1
	if target_doc_id > pst['doc_ids'][new_idx]:
		return new_idx, None

	#loop between idx and new_idx (exclusive) to find if there's a match
	for i in range(idx + 1, new_idx):
		if target_doc_id == pst['doc_ids'][i]:
			return i, target_doc_id

		if target_doc_id < pst['doc_ids'][i]:
			return i, None

	return new_idx, None

def getCommonPosting(pst1, pst2):
	idx1 = 0
	idx2 = 0
	new_doc_ids = []
	# print('pst1/2', pst1, pst2)
	while idx1 < len(pst1['doc_ids']) and idx2 < len(pst2['doc_ids']):
		pst1_doc_id = pst1['doc_ids'][idx1]
		pst2_doc_id = pst2['doc_ids'][idx2]

		if pst1_doc_id == pst2_doc_id:
			new_doc_ids.append(pst1_doc_id)
			idx1 += 1
			idx2 += 1
		elif idx1 == len(pst1['doc_ids']) - 1 or idx2 == len(pst2['doc_ids']) - 1:
			break
		elif pst1_doc_id > pst2_doc_id:
			idx2, doc_id = findMatch(idx2, pst2, pst1_doc_id)
			if doc_id is not None:
				new_doc_ids.append(doc_id)
			idx1 += 1
		else:
			idx1, doc_id = findMatch(idx1, pst1, pst2_doc_id)
			if doc_id is not None:
				new_doc_ids.append(doc_id)
			idx2 += 1

	# return new posting
	posting_len = len(new_doc_ids)
	interval = 0 if posting_len == 0 else math.floor((posting_len - 1) / math.floor(math.sqrt(posting_len)))
	return {
		'doc_ids': new_doc_ids,
		'interval': interval
	}

def andOperation(dict_entries, min_index):
	min_dict_entry = dict_entries[min_index]
	if min_dict_entry.get('doc_freq') == 0:
		return { 'doc_freq': 0, 'posting': [] }
	min_posting = getPostingFromDictEntry(min_dict_entry)
	for idx, entry in enumerate(dict_entries):
		if idx == min_index:
			continue
		cur_posting = getPostingFromDictEntry(entry)
		min_posting = getCommonPosting(min_posting, cur_posting)
		print('MIN POSTING', min_posting)
	return min_posting

def handleQuery(query):
	print('===============')
	print('query: ', query)
	processed_query = shuntingYard(query.split(' '))

	skip_to_idx = 0;
	# for idx, item in enumerate(processed_query):
	idx = 0
	while idx < len(processed_query):
		item = processed_query[idx]
		# if idx < skip_to_idx:
		# 	continue;
		if item == 'NOT':
			idx += 1
			continue
		elif item == 'AND':
			consecutive_and = 1
			offset = 1
			while idx + offset < len(processed_query) and processed_query[idx + offset] == 'AND':
				consecutive_and += 1
				offset += 1

			min_freq = -1
			min_index = -1
			start_index = idx - consecutive_and - 1
			for i in range(start_index, idx):
				if min_freq == -1 or processed_query[i]['doc_freq'] < min_freq:
					min_freq = processed_query[i]['doc_freq']
					min_index = i
			new_posting = andOperation(processed_query[start_index : idx], min_index - start_index)

			# replace from start_index to idx + consecutive_and - 1 to entry with new_posting
			new_dict_entry = {
					'posting': new_posting,
					'doc_freq': len(new_posting['doc_ids'])
				}
			processed_query = processed_query[ 0 : start_index ] +\
			 	[new_dict_entry] + processed_query[idx + consecutive_and:]
			print('new processed_query', processed_query)
			idx = start_index
		elif item == 'OR':
			idx += 1
			continue
		else:
			idx += 1



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
