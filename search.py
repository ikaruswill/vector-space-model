from nltk.stem.porter import PorterStemmer
import io
import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer
import math
from copy import deepcopy

import random

operator_precedence_table = {
	'NOT': 3,
	'AND': 2,
	'OR' : 1,
}

dictionary = {}
postings_file = None
postings_sizes = []
starting_byte_offset = 0
all_doc_ids = []

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
			while len(operator_stack) > 0:
				if operator_stack[0] == '(':
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
	stem = stemmer.stem(term.lower())
	return {'doc_freq': 0} if dictionary.get(stem) is None else dictionary[stem]

def getPosting(index_of_term):
	# calculate byte offset
	posting_offset = 0 if index_of_term - 1 < 0 else postings_sizes[index_of_term - 1]
	byte_offset = starting_byte_offset + posting_offset
	postings_file.seek(byte_offset, 0)
	posting = pickle.load(postings_file)
	return posting

def getNotPosting(pst):
	new_doc_ids = [doc_id for doc_id in all_doc_ids if doc_id not in pst['doc_ids']]
	return {
			'doc_ids': new_doc_ids,
			'interval': getInterval(len(new_doc_ids))
		}

def getPostingFromDictEntry(dict_entry, has_not = False):
	posting = {}
	if dict_entry.get('posting') is not None:
		posting = dict_entry['posting']
	elif dict_entry.get('index') is not None:
		posting = getPosting(dict_entry['index'])
	elif has_not:
		return { 'doc_ids': all_doc_ids }
	else:
		return { 'doc_ids': [] }

	if has_not == True:
		return getNotPosting(posting)
	return posting

def findMatch(idx, pst, target_doc_id):
	has_skip = idx % (pst['interval'] + 1) == 0
	new_idx = min( idx + pst['interval'] + 1, len(pst['doc_ids']) - 1 ) if has_skip else idx + 1
	if int(target_doc_id) > int(pst['doc_ids'][new_idx]):
		return new_idx, None

	#loop between idx and new_idx (exclusive) to find if there's a match
	for i in range(idx + 1, new_idx):
		if target_doc_id == pst['doc_ids'][i]:
			return i + 1, target_doc_id

		if int(target_doc_id) < int(pst['doc_ids'][i]):
			return i, None

	return new_idx, None

def getCommonPosting(pst1, pst2):
	idx1 = 0
	idx2 = 0
	new_doc_ids = []
	while idx1 < len(pst1['doc_ids']) and idx2 < len(pst2['doc_ids']):
		pst1_doc_id = pst1['doc_ids'][idx1]
		pst2_doc_id = pst2['doc_ids'][idx2]

		if pst1_doc_id == pst2_doc_id:
			new_doc_ids.append(pst1_doc_id)
			idx1 += 1
			idx2 += 1
		elif idx1 == len(pst1['doc_ids']) - 1 or idx2 == len(pst2['doc_ids']) - 1:
			break
		elif int(pst1_doc_id) > int(pst2_doc_id):
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
	return {
			'doc_ids': new_doc_ids,
			'interval': getInterval(len(new_doc_ids))
		}

def getInterval(posting_len):
	return 0 if posting_len == 0 else math.floor((posting_len - 1) / math.floor(math.sqrt(posting_len)))

def removePostingDocIds(pst1, pst2):
	new_doc_ids = [doc_id for doc_id in pst1['doc_ids'] if doc_id not in pst2['doc_ids']]
	return {
			'doc_ids': new_doc_ids,
			'interval': getInterval(len(new_doc_ids))
		}

def andOperation(dict_entries, min_freq_index):
	min_dict_entry = dict_entries[min_freq_index]
	if min_dict_entry.get('doc_freq') == 0:
		return { 'interval': 0, 'doc_ids': [] }
	min_posting = getPostingFromDictEntry(min_dict_entry, min_dict_entry.get('has_not'))
	for idx, entry in enumerate(dict_entries):
		if idx == min_freq_index:
			continue
		cur_posting = getPostingFromDictEntry(entry)

		if cur_posting.get('has_not'):
			min_posting = removePostingDocIds(min_posting, cur_posting)
		else:
			min_posting = getCommonPosting(min_posting, cur_posting)
		print('MIN POSTING', min_posting)
	return min_posting

def orOperation(dict_entries):
	pst1 = getPostingFromDictEntry(dict_entries[0], dict_entries[0].get('has_not'))
	pst2 = getPostingFromDictEntry(dict_entries[1], dict_entries[1].get('has_not'))

	new_doc_ids = pst1['doc_ids'] + list(set(pst2['doc_ids']) - set(pst1['doc_ids']))
	# return new posting
	return {
			'doc_ids': new_doc_ids,
			'interval': getInterval(len(new_doc_ids))
		}

def notOperation(dict_entry):
	new_dict = deepcopy(dict_entry)
	new_dict['has_not'] = True
	return new_dict

def handleQuery(query):
	print('=====================================')
	print('query: ', query)
	processed_query = shuntingYard(query.split(' '))

	skip_to_idx = 0;
	# for idx, item in enumerate(processed_query):
	idx = 0
	while idx < len(processed_query):
		item = processed_query[idx]
		if item == 'NOT':
			start_index = idx - 1
			new_dict_entry = notOperation(processed_query[start_index])
			processed_query = processed_query[ 0 : start_index ] +\
			 	[new_dict_entry] + processed_query[idx + 1:]
			idx = start_index
			continue
		elif item == 'AND':
			consecutive_and = 1
			offset = 1
			while idx + offset < len(processed_query) and processed_query[idx + offset] == 'AND':
				consecutive_and += 1
				offset += 1

			min_freq = -1
			min_freq_index = -1
			start_index = idx - consecutive_and - 1
			max_has_not_freq = -1
			max_has_not_index = -1

			for i in range(start_index, idx):
				if processed_query[i].get('has_not') == True:
					if max_has_not_freq == -1 or processed_query[i]['doc_freq'] > max_has_not_freq:
						max_has_not_freq = processed_query[i]['doc_freq']
						max_has_not_index = i
					continue
				if min_freq == -1 or processed_query[i]['doc_freq'] < min_freq:
					min_freq = processed_query[i]['doc_freq']
					min_freq_index = i

			new_posting = {}
			if min_freq_index == -1:
				new_posting = andOperation(processed_query[start_index : idx], max_has_not_index - start_index)
			else:
				new_posting = andOperation(processed_query[start_index : idx], min_freq_index - start_index)

			# replace from start_index to idx + consecutive_and - 1 to entry with new_posting
			new_dict_entry = {
					'posting': new_posting,
					'doc_freq': len(new_posting['doc_ids'])
				}
			processed_query = processed_query[ 0 : start_index ] +\
			 	[new_dict_entry] + processed_query[idx + consecutive_and:]
			# print('new processed_query', processed_query)
			idx = start_index
		elif item == 'OR':
			start_index = idx - 2
			new_posting = orOperation(processed_query[start_index : idx])
			new_dict_entry = {
					'posting': new_posting,
					'doc_freq': len(new_posting['doc_ids'])
				}
			processed_query = processed_query[ 0 : start_index ] +\
			 	[new_dict_entry] + processed_query[idx + 1:]
			# print('new processed_query', processed_query)
			idx = start_index
			continue
		else:
			idx += 1

	# print('final', processed_query)

	if processed_query[0].get('posting') is None:
		return getPostingFromDictEntry(processed_query[0], processed_query[0].get('has_not'))['doc_ids']

	if processed_query[0].get('has_not') is True:
		return getPostingFromDictEntry(processed_query[0], True)['doc_ids']

	return processed_query[0]['posting']['doc_ids']

def addSpaceForBrackets(query):
	new_query = ''
	for i, char in enumerate(query):
		if char == '(' and i + 1 < len(query) and query[i + 1] != ' ':
			new_query += '( '
		elif char == ')' and i - 1 >= 0 and query[i - 1] != ' ':
			new_query += ' )'
		else:
			new_query += char
	return new_query

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
	all_doc_ids = getPostingFromDictEntry(getDictionaryEntry('*'))['doc_ids']

	print('***QUERY RESULT***')

	output_file = io.open(output_path, 'w')
	with io.open(query_path, 'r') as f:
		for line in f:
			line = line.strip()
			if line != '':
				try:
					query = addSpaceForBrackets(line.strip())
					result = handleQuery(query)
					# print('len', len(result))
					output = ' '.join(result)
					print('output', output)
					output_file.write(output + '\n')
				except Exception as e:
					output_file.write('\n')
					print('****** WARN EXCEPTION ******', e)
					continue

	postings_file.close()

	print('++ 3 Random items in dictionary ++')
	for i in range(3):
		print(random.choice(list(dictionary.items())))