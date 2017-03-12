# /bin/sh

if hash python3 >/dev/null
then
	py_cmd="python3"
else
	py_cmd="python"
fi

$py_cmd index.py -i ~/nltk_data/corpora/reuters/training -d dictionary.txt -p postings.txt -l lengths.txt
