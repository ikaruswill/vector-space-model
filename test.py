from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from pprint import pprint
import math

postings = {
    'of' : [('1', 8), ('6', 2), ('9', 4), ('10', 10), ('11', 1), ('12', 7), ('13', 2), ('18', 8), ('19', 3), ('22', 1), ('23', 5), ('24', 1), ('27', 2), ('29', 6), ('30', 2), ('37', 1), ('40', 1), ('41', 2), ('42', 1), ('44', 3), ('45', 8), ('46', 1), ('47', 5), ('49', 1), ('50', 1)],
    'sell' : [('1', 1)],
    'again' : [('1', 1)],
    'mine' : [('22', 1)],
    'high' : [('45', 1)],
    'john' : [('29', 1)],
    'in' : [('1', 6), ('6', 2), ('9', 1), ('12', 5), ('18', 7), ('19', 2), ('23', 4), ('27', 1), ('29', 3), ('30', 2), ('37', 1), ('40', 6), ('42', 1), ('44', 1), ('45', 7), ('46', 2), ('47', 4), ('48', 4), ('49', 1)],
    'to' : [('1', 14), ('6', 2), ('9', 3), ('10', 9), ('12', 4), ('18', 6), ('19', 3), ('22', 2), ('23', 7), ('24', 1), ('29', 2), ('37', 1), ('40', 3), ('42', 4), ('44', 4), ('45', 7), ('46', 2), ('47', 7), ('48', 1), ('49', 2)],
    'it' : [('1', 2), ('9', 3), ('10', 9), ('12', 4), ('18', 3), ('19', 1), ('22', 2), ('23', 4), ('27', 1), ('40', 1), ('44', 2), ('45', 4), ('47', 3), ('48', 1), ('49', 2), ('50', 1)],
    'for' : [('1', 10), ('5', 3), ('6', 2), ('9', 1), ('10', 4), ('13', 2), ('18', 3), ('19', 2), ('23', 2), ('27', 1), ('40', 1), ('41', 2), ('42', 3), ('44', 1), ('45', 5), ('46', 1), ('47', 2)],
    'said' : [('1', 5), ('9', 2), ('10', 7), ('12', 5), ('18', 6), ('19', 2), ('22', 1), ('23', 5), ('29', 3), ('40', 1), ('42', 3), ('44', 2), ('45', 9), ('46', 2), ('47', 1), ('48', 1), ('49', 1), ('50', 1)],
    'intern' : [('13', 1), ('42', 1)],
    'agricultur' : [('5', 1), ('19', 1), ('46', 1)],
    'comput' : [('10', 7), ('37', 1)],
    'analyst' : [('18', 2), ('45', 2)],
    'economi' : [('40', 1), ('47', 3)],
    'currenc' : [('1', 2), ('47', 1)],
    'trade' : [('1', 1), ('45', 1), ('47', 3)],
    'quota' : [('42', 2), ('46', 5)],
    'strong' : [('18', 1), ('23', 1), ('45', 1)],
    'purchas' : [('10', 1), ('19', 1)]
}
doc_norm = {'9': 7.498062117411825, '40': 9.195903685171558, '47': 12.783414508606624, '37': 7.485767395024795, '23': 12.491295963899482, '42': 9.194382210562276, '18': 14.054438715213243, '27': 7.888389131381812, '10': 12.620579454917959, '19': 8.687094317196655, '29': 9.348515672270713, '11': 7.036456224049258, '30': 4.690930360283176, '5': 10.82940342262473, '45': 17.047946654588124, '24': 7.783108881614609, '12': 10.729940615602505, '14': 6.026221133349604, '13': 9.26119391864431, '1': 18.458729103872535, '6': 12.119870972167787, '38': 6.319073982041696, '22': 5.6142540644322185, '46': 9.44555665354, '49': 8.510253017076316, '36': 4.698727183913986, '48': 6.355609008284731, '50': 6.216532992692284, '41': 8.303853948806838, '44': 8.651931461191667}

def preprocess_query(query):
    stemmer = PorterStemmer()
    output = {}
    for token in word_tokenize(query):
        stem = stemmer.stem(token)
        if output.get(stem) is None:
            output[stem] = 1
        else:
            output[stem] += 1
    return output

def test(query):
    query_tf_dict = preprocess_query(query)
    query_weights = []
    scores = {}
    for term, query_tf in query_tf_dict.items():
        if term in postings:
            query_tf_weight = math.log10(query_tf) + 1
            idf = math.log10(float(len(doc_norm)) / len(postings[term]))
            query_weight = query_tf_weight * idf
            query_weights.append(query_weight)
            for doc_id, doc_freq in postings[term]:
                doc_tf_weight = 1 + math.log10(doc_freq)
                if scores.get(doc_id) is None:
                    scores[doc_id] = 0
                scores[doc_id] += doc_tf_weight * query_weight

    query_length = math.sqrt(sum([math.pow(query_weight, 2) for query_weight in query_weights]))
    for doc_id in scores:
        scores[doc_id] /= doc_norm[doc_id] * query_length

    tuplescores = [(-score, doc_id) for doc_id, score in scores.items()]
    tuplescores.sort()
    docids = [doc_id for score, doc_id in tuplescores[:min(len(tuplescores), 10)]]
    print(' '.join(docids))


while True:
    input = raw_input('query: ')
    test(input)
