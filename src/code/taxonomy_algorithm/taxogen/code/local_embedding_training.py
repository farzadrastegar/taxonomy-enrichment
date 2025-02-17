#!/usr/bin/env
'''
__author__: Chao Zhang
__description__: Run local embedding using word2vec
__latest_updates__: 09/26/2017
__Modified by : Mili Biswas (UNIFR)
__update date : May 2020 
'''
import numpy as np
import argparse
import subprocess
import utils
import os
from gensim.models import FastText


np.random.seed(0)
PYTHONHASHSEED=0

#----------------------------------------------------------------------------------------------------------------------------
# Modified by Mili Biswas, for Taxonomy Building based on Fashion Data (Amazon Review + FashionBlog)
#----------------------------------------------------------------------------------------------------------------------------

def save(model,path):
        #self.model.save(path)
        print('[Info]: The word2vec trained model is saved at ',path)
        model.wv.save_word2vec_format(path)

def word2vec(inputFile,outputFile,SIZE,SAMPLE,WINDOW,MIN_COUNT,ITER):
    '''
        This function triggers the FastText model
        Parameters:
                 1. inputFile => This is corpus data as input file  
                 2. outputFile => Output file 
                 3. size => embedding dimension size
                 4. window => window size for context (skip-gram)
                 5. min_count => minimum number of word count to be considered
                 6. epoch => number of times the algorithm will run
                 7. down_sampling => value for down_sampling
    '''
    print('inputFile:'+inputFile)
    print('outputFile:'+outputFile)
    corpus=[]
    with open(inputFile,'r') as fin:
        for blog in fin:
            corpus.append(blog.strip('\n'))

    word_tokenized_corpus = [review.split() for review in corpus]
    
    
    try:
        model = FastText(size=SIZE, window=WINDOW, min_count=MIN_COUNT,seed=0,workers=1,max_n=0)   # instantiate the fasttext model (max_n added by Farzad)
        model.build_vocab(sentences=word_tokenized_corpus)                                 # build the vocabulary
        model.train(
                    sentences=word_tokenized_corpus, 
                    total_examples=len(word_tokenized_corpus),
                    sg=1,
                    sample=SAMPLE, 
                    epochs=ITER
                  )
        
        
        word_vectors=[]
        for w in model.wv.vocab:
            try:
                word_vectors.append(model[w])
            except Exception as err:
                print(str(err)+": "+ w)
                continue
            
        no_of_words=len(model.wv.vocab)
        dimension=SIZE

        with open(outputFile,'w') as fout:
            fout.write(str(no_of_words)+' '+str(dimension)+'\n')
            for i,w in enumerate(model.wv.vocab):
                fout.write(w)
                for feature in word_vectors[i]:
                    fout.write(' '+str(feature))
                fout.write('\n')
        
    except Exception as err:
        print(err)
    return model       # Changed here from None to model


def read_files(folder, parent):
    print("[Local-embedding] Reading file:", parent)
    emb_file = '%s/embeddings.txt' % folder
    hier_file = '%s/hierarchy.txt' % folder
    keyword_file = '%s/keywords.txt' % folder ## here only consider those remaining keywords

    embs = utils.load_embeddings(emb_file)
    keywords = set()
    cates = {}

    with open(keyword_file) as f:
        for line in f:
            keywords.add(line.strip('\r\n'))

    tmp_embs = {}
    for k in keywords:
        if k in embs:
            tmp_embs[k] = embs[k]
    embs = tmp_embs

    with open(hier_file) as f:
        for line in f:
            segs = line.strip('\r\n').split(' ')
            if segs[1] == parent and segs[0] in embs: #fixed a bug by Farzad
                cates[segs[0]] = set()

    print('[Local-embedding] Finish reading embedding, hierarchy and keywords files.')

    return embs, keywords, cates

def relevant_phs(embs, cates, N):

    for cate in cates:
        worst = -100
        bestw = [-100] * (N + 1)
        bestp = [''] * (N + 1)
        # cate_ph = cate[2:]
        cate_ph = cate

        for ph in embs:
            sim = utils.cossim(embs[cate_ph], embs[ph])
            if sim > worst:
                for i in range(N):
                    if sim >= bestw[i]:
                        for j in range(N - 1, i - 1, -1):
                            bestw[j+1] = bestw[j]
                            bestp[j+1] = bestp[j]
                        bestw[i] = sim
                        bestp[i] = ph
                        worst = bestw[N-1]
                        break

        # print bestw
        # print bestp

        for ph in bestp[:N]:
            cates[cate].add(ph)

    print('Top similar phrases found.')

    return cates

def revevant_docs(text, reidx, cates):
    docs = {}
    idx = 0
    pd_map = {}
    for cate in cates:
        for ph in cates[cate]:
            pd_map[ph] = set()

    with open(text) as f:
        for line in f:
            docs[idx] = line
            idx += 1

    with open(reidx) as f:
        for line in f:
            segments = line.strip('\r\n').split('\t')
            doc_ids = segments[1].split(',')
            if len(doc_ids) > 0 and doc_ids[0] == '':
                continue
                # print line
            pd_map[segments[0]] = set([int(x) for x in doc_ids])

    print('Relevant docs found.')

    return pd_map, docs


def run_word2vec(pd_map, docs, cates, folder, level, MAX_LEVEL,SIZE,SAMPLE,WINDOW,MIN_COUNT,ITER):

    for cate in cates:

        c_docs = set()
        for ph in cates[cate]:
            c_docs = c_docs.union(pd_map[ph])

        print('Starting cell %s with %d docs.' % (cate, len(c_docs)))
        
        # save file
        # sub_folder = '%s/%s' % (folder, cate)
        # input_f = '%s/text' % sub_folder
        # output_f = '%s/embeddings.txt' % sub_folder
        sub_folder = folder + cate + '/'
        input_f = sub_folder + 'text'
        output_f = sub_folder + 'embeddings.txt'
        if not os.path.exists(sub_folder):
            os.makedirs(sub_folder)
        with open(input_f, 'w+') as g:
            for d in c_docs:
                g.write(docs[d])

        print('[Local-embedding] starting calling word2vec')
        print(input_f)
        print(output_f)
        # embed_proc = subprocess.Popen(["./word2vec", "-threads", "20", "-train", input_f, "-output", output_f], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # embed_proc.wait()
        #subprocess.call(["./word2vec", "-threads", "20", "-train", input_f, "-output", output_f,"-size","60"])
        model=word2vec(input_f,output_f,SIZE,SAMPLE,WINDOW,MIN_COUNT,ITER)
        print('[Local-embedding] done training word2vec')
        
        if level==(MAX_LEVEL-3):
            save(model,os.path.join('../../../../data/tmp/local_embeds',cate))


def main_local_embedding(folder, doc_file, reidx, parent, N,level,MAX_LEVEL,SIZE,SAMPLE,WINDOW,MIN_COUNT,ITER):
    embs, keywords, cates = read_files(folder, parent)
    cates = relevant_phs(embs, cates, int(N))
    pd_map, docs = revevant_docs(doc_file, reidx, cates)
    run_word2vec(pd_map, docs, cates, folder,level,MAX_LEVEL,SIZE,SAMPLE,WINDOW,MIN_COUNT,ITER)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='local_embedding_training.py', \
            description='Train Embeddings for each query.')
    parser.add_argument('-folder', required=True, \
            help='The folder of previous level.')
    parser.add_argument('-text', required=True, \
            help='The raw text file.')
    parser.add_argument('-reidx', required=True, \
            help='The reversed index file.')
    parser.add_argument('-parent', required=True, \
            help='the target expanded phrase')
    parser.add_argument('-N', required=True, \
            help='The number of neighbor used to extract documents')
    args = parser.parse_args()
    main_local_embedding(args.folder, args.text, args.reidx, args.parent, args.N)


# python local_embedding_training.py -folder ../data/cluster -text ../data/paper_phrases.txt.frequent.hardcode -reidx ../data/reidx.txt -parent \* -N 100

