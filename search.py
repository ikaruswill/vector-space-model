import io
import getopt
import sys
import pickle
from nltk.stem.porter import PorterStemmer
import math
from copy import deepcopy

dictionary = {}
postings_file = None
postings_sizes = []
starting_byte_offset = 0
all_doc_ids = []

def usage():
	print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

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

	if new_idx >= len(pst['doc_ids']) or int(target_doc_id) > int(pst['doc_ids'][new_idx]):
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
		elif idx1 == len(pst1['doc_ids']) - 1 and idx2 == len(pst2['doc_ids']) - 1:
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

def handleQuery(query):
	pass

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

	output_file = io.open(output_path, 'w')
	with io.open(query_path, 'r') as f:
		for line in f:
			line = line.strip()
			if line != '':
				try:
					result = handleQuery(query)
					output = ' '.join(result)
					output_file.write(output + '\n')
				except Exception as e:
					output_file.write('\n')
					continue

	output_file.close()
	postings_file.close()
