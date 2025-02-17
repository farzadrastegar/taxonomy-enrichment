'''
__author__: Chao Zhang
__description__: A wrapper for spherecluster, implement the term clustering component.
__latest_updates__: 09/25/2017
__Modified by:  Mili Biswas (UNIFR)
__update date:  May 2020
'''
from collections import defaultdict
import numpy as np

np.random.seed(0)
PYTHONHASHSEED=0

from scipy.spatial.distance import cosine
from spherecluster import SphericalKMeans
#from sklearn.cluster import KMeans
from dataset import SubDataSet

class Clusterer:

    def __init__(self, data, n_cluster):
        self.data = data
        self.n_cluster = n_cluster
        self.clus = SphericalKMeans(n_cluster,random_state=0) # Change by Mili (added Random State)
        #self.clus = KMeans(n_cluster)
        self.clusters = defaultdict(list)  # cluster id -> members
        self.membership = None  # a list contain the membership of the data points
        self.center_ids = None  # a list contain the ids of the cluster centers
        self.inertia_scores = None
        self.old2new_clusterid=None

    def fit(self):
        self.clus.fit(self.data)
        #labels = self.clus.labels_
        self.old2new_clusterid=self.old2new_clusteridx() # Change by Mili
        #print('old label',self.clus.labels_)
        labels=self.get_new_label(self.clus.labels_)
        self.clus.labels_=labels
        #print('new label',labels)
        for idx, label in enumerate(labels):
            self.clusters[label].append(idx)
        self.membership = labels
        self.center_ids = self.gen_center_idx()
        self.inertia_scores = self.clus.inertia_
        print('Clustering concentration score:', self.inertia_scores)

    # find the idx of each cluster center
    def gen_center_idx(self):
        ret = []
        for cluster_id in range(self.n_cluster):
            #cluster_id=self.old2new_clusterid[cluster_id]   # Change by mili
            center_idx = self.find_center_idx_for_one_cluster(cluster_id)
            ret.append((cluster_id, center_idx))
        return ret


    def find_center_idx_for_one_cluster(self, cluster_id):
        query_vec = self.clus.cluster_centers_[cluster_id]
        members = self.clusters[cluster_id]
        best_similarity, ret = -1, -1
        for member_idx in members:
            member_vec = self.data[member_idx]
            cosine_sim = self.calc_cosine(query_vec, member_vec)
            if cosine_sim > best_similarity:
                best_similarity = cosine_sim
                ret = member_idx
        return ret

    def calc_cosine(self, vec_a, vec_b):
        return 1 - cosine(vec_a, vec_b)
    
    '''
        The below functions is created by Mili Biswas
    '''
    
    def get_new_label(self,old_label):
        
        newLabel=[self.old2new_clusterid[e] for e in old_label]    
        return newLabel
    
    
    '''
        The below functions is created by Mili Biswas
    '''
    
    def old2new_clusteridx(self):
        old2new_clusterIdx={}
        clusterIdx=np.argsort(self.clus.cluster_centers_.sum(axis=1))
        print('cluster centre',self.clus.cluster_centers_.sum(axis=1))
        self.set_Cluster_Center(clusterIdx)
        for new,old in enumerate(clusterIdx):
            if old not in old2new_clusterIdx:
                old2new_clusterIdx[old]=''
            old2new_clusterIdx[old]=new
        return old2new_clusterIdx
    
    def set_Cluster_Center(self,clusterIdx):
        old_center=self.clus.cluster_centers_
        new_center=[]
        for id in clusterIdx:
            new_center.append(old_center[id])
            
        self.clus.cluster_centers_=np.array(new_center)
        return None
        

def run_clustering(full_data, doc_id_file, filter_keyword_file, n_cluster, parent_direcotry, parent_description,\
                   cluster_keyword_file, hierarchy_file, doc_membership_file):
    dataset = SubDataSet(full_data, doc_id_file, filter_keyword_file)
    print('Start clustering for ', len(dataset.keywords), ' keywords under parent:', parent_description)
   
    #added by Farzad 
    if len(dataset.keywords) < n_cluster:
        n_cluster = len(dataset.keywords)
        
    ## TODO: change later here for n_cluster selection from a range
    clus = Clusterer(dataset.embeddings, n_cluster)
    clus.fit()
    print('Done clustering for ', len(dataset.keywords), ' keywords under parent:', parent_description)
    dataset.write_cluster_members(clus, cluster_keyword_file, parent_direcotry)
    center_names = dataset.write_cluster_centers(clus, parent_description, hierarchy_file)
    dataset.write_document_membership(clus, doc_membership_file, parent_direcotry)
    print('Done saving cluster results for ', len(dataset.keywords), ' keywords under parent:', parent_description)
    return center_names
