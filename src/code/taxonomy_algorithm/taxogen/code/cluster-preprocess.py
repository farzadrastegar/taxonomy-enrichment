'''
__author__: Chao Zhang
__description__:
__latest_updates__: 09/26/2017
'''
import sys
from collections import Counter

def trim_keywords(raw_keyword_file, keyword_file, embedding_file):
    '''

    :param raw_keyword_file: input keyword file
    :param keyword_file: output keyword file (intersection of raw keywords and embedding keywords)
    :param embedding_file: input embedding file
    :return:
    '''
    keywords = load_keywords(raw_keyword_file)
    embedded_keywords = load_embedding_keywords(embedding_file)
    with open(keyword_file, 'w') as fout:
        for w in keywords:
            if w in embedded_keywords:
                fout.write(w + '\n')

def load_keywords(seed_word_file):
    seed_words = []
    with open(seed_word_file, 'r') as fin:
        for line in fin:
            seed_words.append(line.strip())
    return seed_words

def load_embedding_keywords(embedding_file):
    keyword_set = set()
    with open(embedding_file, 'r') as fin:
        header = fin.readline()
        for line in fin:
            items = line.strip().split()
            word = items[0]
            keyword_set.add(word)
    return keyword_set


def trim_document_set(raw_doc_file, doc_file, keyword_file, doc_idx_in_raw_doc_file):
    ''' A document is included only if it contains one or more keywords

    :param raw_doc_file:
    :param doc_file:
    :param keyword_file:
    :return:
    '''
    keyword_set = set(load_keywords(keyword_file))
    with open(raw_doc_file, 'r') as fin, open(doc_file, 'w') as fout, open(doc_idx_in_raw_doc_file, 'w') as fout2:
        raw_doc_line_number = -1
        doc_line_number = -1
        non_existing_raw_doc_count = 0
        for line in fin:
            raw_doc_line_number += 1
            doc = line.strip().split()
            if check_doc_contain_keyword(doc, keyword_set):
                doc_line_number += 1
                fout.write(' '.join(doc) + '\n')
                fout2.write(str(doc_line_number)+','+str(raw_doc_line_number)+'\n')
            else:
                non_existing_raw_doc_count -= 1
                fout2.write(str(non_existing_raw_doc_count)+','+str(raw_doc_line_number)+'\n')

def check_doc_contain_keyword(doc, keyword_set):
    ''' check whether a document contains one or more keywords

    :param doc: a list of tokens
    :param keyword_set: a set of keywords
    :return: True/False
    '''
    for word in doc:
        if word in keyword_set:
            return True
    return False


def gen_doc_keyword_cnt_file(doc_file, keyword_cnt_file):
    documents = []
    with open(doc_file, 'r') as fin:
        for line in fin:
            keywords = line.strip().split()
            documents.append(keywords)
    doc_word_counts = []
    for d in documents:
        c = Counter(d)
        doc_word_counts.append(c)

    with open(keyword_cnt_file, 'w') as fout:
        for i, counter in enumerate(doc_word_counts):
            counter_string = counter_to_string(counter)
            fout.write(str(i) + '\t' + counter_string + '\n')


def counter_to_string(counter):
    elements = []
    for k, v in counter.items():
        elements.append(k)
        elements.append(v)
    return '\t'.join([str(e) for e in elements])


def gen_doc_ids(input_file, output_file):
    doc_id = 0
    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line in fin:
            fout.write(str(doc_id)+"\n")
            doc_id += 1


def main(raw_dir, input_dir, init_dir):
    ## Following are three required input files
    raw_doc_file = raw_dir + 'papers.txt'
    raw_keyword_file = raw_dir + 'keywords.txt'
    embedding_file = input_dir + 'embeddings.txt'

    ## Following are four output files
    doc_file = input_dir + 'papers.txt'
    doc_idx_in_raw_doc_file = input_dir + 'papers_idx_in_raw.txt'
    keyword_file = input_dir + 'keywords.txt'
    doc_keyword_cnt_file = input_dir + 'keyword_cnt.txt'
    doc_id_file = init_dir + 'doc_ids.txt'

    trim_keywords(raw_keyword_file, keyword_file, embedding_file)
    print('Done trimming the keywords.')

    trim_document_set(raw_doc_file, doc_file, keyword_file, doc_idx_in_raw_doc_file)
    print('Done trimming the documents.')

    gen_doc_keyword_cnt_file(doc_file, doc_keyword_cnt_file)
    print('Done counting the keywords in documents.')

    gen_doc_ids(doc_file, doc_id_file)
    print('Done generating the doc ids.')

# raw_dir = '/shared/data/czhang82/projects/local-embedding/sp/raw/'
# input_dir = '/shared/data/czhang82/projects/local-embedding/sp/input/'
# init_dir = '/shared/data/czhang82/projects/local-embedding/sp/init/'
if __name__ == '__main__':
    corpusName = sys.argv[1]
    raw_dir = '../data/'+corpusName+'/raw/'
    input_dir = '../data/'+corpusName+'/input/'
    init_dir = '../data/'+corpusName+'/init/'
    main(raw_dir, input_dir, init_dir)
