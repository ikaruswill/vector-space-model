

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

if __name__ == '__main__':
	dir_doc = dict_file = postings_file = None
	try:
	    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
	except getopt.GetoptError as err:i
	    usage()
	    sys.exit(2)
	for o, a in opts:
	    if o == '-i':
	        dir_doc = a
	    elif o == '-d':
	        dict_file = a
	    elif o == '-p':
	        postings_file = a
	    else:
	        assert False, "unhandled option"
	if input_file_b == None or input_file_t == None or output_file == None:
	    usage()
	    sys.exit(2)