'''
__author__: Mili Biswas
__description__: Main function for TaxonGen
__latest_updates__: 07/09/2020
'''
import time
from dataset import DataSet
from cluster import run_clustering
from paras import *
from caseslim import main_caseolap
from case_ranker import main_rank_phrase
from local_embedding_training import main_local_embedding
from shutil import copyfile
from distutils.dir_util import copy_tree
from os import symlink
import sys
import os
import ast

PYTHONHASHSEED=0

class DataFiles:
    
    def __init__(self, input_dir, node_dir):
        self.doc_file = input_dir + 'papers.txt'
        self.link_file = input_dir + 'keyword_cnt.txt'
        self.index_file = input_dir + 'index.txt'

        self.embedding_file = node_dir + 'embeddings.txt'
        self.seed_keyword_file = node_dir + 'seed_keywords.txt'
        self.doc_id_file = node_dir + 'doc_ids.txt'

        self.doc_membership_file = node_dir + 'paper_cluster.txt'
        self.hierarchy_file = node_dir + 'hierarchy.txt'
        self.cluster_keyword_file = node_dir + 'cluster_keywords.txt'

        self.caseolap_keyword_file = node_dir + 'caseolap.txt'
        self.filtered_keyword_file = node_dir + 'keywords.txt'


    '''
        input_dir: the directory for storing the input files that do not change
        node_dir: the directory for the current node in the hierarchy
        n_cluster: the number of clusters
        filter_thre: the threshold for filtering general keywords in the caseolap phase
        parent: the name of the parent node
        n_expand: the number of phrases to expand from the center
        level: the current level in the recursion
    '''
    
def recur(input_dir, node_dir, n_cluster, parent, n_cluster_iter, filter_thre,\
          n_expand, level, caseolap=True, local_embedding=True): 
    
    
    
    if level > MAX_LEVEL:
        return
    #print('============================= Running level ', level, ' and node ', parent, '=============================')
    start = time.time()
    df = DataFiles(input_dir, node_dir)
    
    ## TODO: Everytime we need to read-in the whole corpus, which can be slow.
    
    full_data = DataSet(df.embedding_file, df.doc_file)
    end = time.time()
    #print('[Main] Done reading the full data using time %s seconds' % (end-start))

    # filter the keywords
    if caseolap is False:
        try:
            children = run_clustering(full_data, df.doc_id_file, df.seed_keyword_file, n_cluster, node_dir, parent, \
                                      df.cluster_keyword_file, df.hierarchy_file, df.doc_membership_file)
        except:
            print(children)
            print('Clustering not finished.')
            return
        copyfile(df.seed_keyword_file, df.filtered_keyword_file)
    else:
        ## Adaptive Clustering, maximal n_cluster_iter iterations
        
        n_cluster=clusterInfo.pop(0)            ## Changed by Mili
        
        if n_cluster >0:
            for iter in range(n_cluster_iter):
                if iter > 0:
                    df.seed_keyword_file = df.filtered_keyword_file
                try:
                    children = run_clustering(full_data, df.doc_id_file, df.seed_keyword_file, n_cluster, node_dir, parent,\
                                   df.cluster_keyword_file, df.hierarchy_file, df.doc_membership_file)
                except Exception as err:
                    print('[Error]: Clustering not finished.')
                    print('[Error]: '+str(err))
                    return
    
                start = time.time()
                main_caseolap(df.link_file, df.doc_membership_file, df.cluster_keyword_file, df.caseolap_keyword_file)
                main_rank_phrase(df.caseolap_keyword_file, df.filtered_keyword_file, filter_thre)  
                
                end = time.time()
                #print("[Main] Finish running CaseOALP using %s (seconds)" % (end - start))
        else:
            print('[Info]: Leaf node is reached')

    # prepare the embedding for child level
    
    if n_cluster >0:   #changed by mili
        
        if level < MAX_LEVEL:
            
            if local_embedding is False:
                
                src_file = node_dir + 'embeddings.txt'
                
                for child in children:
                    tgt_file = node_dir + child + '/embeddings.txt'
                    # copyfile(src_file, tgt_file)
                    symlink(src_file, tgt_file)
            else:
                start = time.time()
                main_local_embedding(node_dir, df.doc_file, df.index_file, parent, n_expand,level,MAX_LEVEL,SIZE,SAMPLE,WINDOW,MIN_COUNT,ITER)
                end = time.time()
                #print("[Main] Finish running local embedding training using %s (seconds)" % (end - start))
                
        for child in children:
            recur(input_dir, node_dir + child + '/', n_cluster, child, n_cluster_iter, \
                      filter_thre, n_expand, level + 1, caseolap, local_embedding)

def main(opt):
    input_dir = opt['input_dir']
    init_dir = opt['data_dir'] + 'init/'
    n_cluster = opt['n_cluster']
    filter_thre = opt['filter_thre']
    n_expand = opt['n_expand']
    n_cluster_iter = opt['n_cluster_iter']
    level = 0
    root_dir = opt['data_dir'] + 'our-l3-0.15/'
    copy_tree(init_dir, root_dir)
    recur(input_dir, root_dir, n_cluster, '*', n_cluster_iter, filter_thre, n_expand, level, True, True)

if __name__ == '__main__':
    
    dir_path=sys.argv[1]
    clusterInfo=ast.literal_eval(sys.argv[2])
    MAX_LEVEL=int(sys.argv[3])
    SIZE=int(sys.argv[4])
    SAMPLE=float(sys.argv[5]) 
    WINDOW=int(sys.argv[6]) 
    MIN_COUNT=int(sys.argv[7]) 
    ITER=int(sys.argv[8])
    opt = load_dblp_params_method(dir_path)
    main(opt)