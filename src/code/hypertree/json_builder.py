#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 16:31:21 2020

@author: milibiswas
"""
import numpy as np
import sys
#import re
import os
import json
from nltk import FreqDist

class JsonBuild(object):
    papers_idx_in_raw = {}
    raw_papers = []

    def __init__(self,):

        self.pathList=[]
        self.dataDict=None

    @staticmethod
    def load(path):
        print('mylog: Current directory: ' + os.getcwd())
        print('mylog: path=' + path)

        # read doc->raw_doc indeces in a dictionary
        inputDirParent_input = os.path.join(path, 'input')
        JsonBuild.papers_idx_in_raw = {}
        with open(os.path.join(inputDirParent_input,'papers_idx_in_raw.txt'), 'r') as fin:
            for line in fin:
                # print('mylog3: ' + line)
                lineList = line.strip().split(',')
                if (len(lineList) == 2):
                    JsonBuild.papers_idx_in_raw.update({int(lineList[0]) : int(lineList[1])})

        # read raw papers into a list
        inputDirParent_raw = os.path.join(path, 'raw')
        JsonBuild.raw_papers = []
        with open(os.path.join(inputDirParent_raw,'original_papers.txt'), 'r') as fin:
            for line in fin:
                # print('mylog4: ' + line)
                JsonBuild.raw_papers.append(line.strip())
        
    def createJavaScriptFile(self,path=None):
        try:
            if self.dataDict==None:
                raise Exception
            else:
                with open('./src/data/output/taxonomy.json','w') as fout:
                    json.dump(self.dataDict,fout)
                print('[Info]: Json file created at :','./src/data/output/taxonomy.json')
                
                with open(path,'w') as fout:
                    fout.write('function json_data() {')
                    fout.write('\n')
                    fout.write('var x = ')
                    json.dump(self.dataDict,fout)
                    fout.write(';')
                    fout.write('return x; }')
                print('[Info]: Jason file created at :',path)
        except Exception as err:
            print('Error occurred')
            print(str(err))
            sys.exit(1)
            
# =============================================================================
#     def dumpPathList(self,pathListFile='./output/pathlist.txt'):
#         try:
#             if pathListFile==None:
#                 raise Exception
#             else:
#                 with open(pathListFile,'w') as fout:
#                     for line in self.pathList:
#                         fout.write('-->'.join(line))
#                         fout.write('\n')
#                 print('pathlist data file created at :',pathListFile)
#         except Exception as err:
#             print('Error occurred')
#             print(str(err))
#             sys.exit(1)
# =============================================================================
        
        
# =============================================================================
    def __rootToLeafPath(self,inputTree,nameStr=''):
         '''
             This function will produce a list of lists
             where each individual inner list is a distinct
             path from root to leaves
         '''
         if nameStr=='':
             nameStr=inputTree['name']
         else:
             nameStr=nameStr+'#'+inputTree['name']
             
         if len(inputTree['children'])>0:
             for child in inputTree['children']:
                 self.__rootToLeafPath(child,nameStr)
         else:
             self.pathList.append(nameStr.split('#'))
         
         return None
# =============================================================================
    
    def __nodeRenameAlgorithm(self,seedFile):
        '''
            This function implements node rename algorithm which the json builder
            will use subsequently to generate the Taxonomy & Publish in JavaScript
            HyperTree.
        
        '''
        #print("========================= Starting nodeRenameAlgorithm() function ==========================")
        wordList=[]
        with open(seedFile,'r') as fin:
            for line in fin:
                keyWord=line.strip().strip('\n')
                if '_' in keyWord:
                    temp=keyWord.split('_')
                    wordList += temp
                else:
                    wordList.append(keyWord)
                    
        # Frequency Distribution of words
        
        dist=FreqDist(wordList)
        
        nodeNamesList=[]
        for w,val in dist.most_common(2):
            if val>1:
                nodeNamesList.append(w)
            else:
                nodeNamesList.append('other')
            
        return ' & '.join(list(set(nodeNamesList)))
    
    def jsonBuilder(self,inputDir=None,parent='*',level=1,parentVec=None):
    
        dataDict={}
        if parent=='*':
            pass
        else:
            #parent=self.__nodeRenameAlgorithm(os.path.join(inputDir,'seed_keywords.txt'))
            pass
        
        '''
            1. Read parent/root directory
            2. Locate hierarchy File in the directory
            3. Read Hierarchy file
            4. Populate general fields from the directory + Hierarchy file
            5. If there are children from hierarchy, call the self function for each child.
            6. Add each childs return dict into a list (children list maintained in parent)
    
        '''

        if os.path.exists(os.path.join(inputDir,'hierarchy.txt')):
            children=[]
            #parent=''
                
            with open(os.path.join(inputDir,'hierarchy.txt'),'r') as fin:
                for line in fin:
                    child,parent1=line.strip().split()
                    children.append(child)
                    parent=parent
            dataDict['id']=parent        
            dataDict['name']=parent
            dataDict['center']=parentVec
            dataDict['children']=[]
            
            # Other than root level, we need data element
            if level>1:
                dataDict['data']={"type":"concept","depth":level}
                
            else:
                dataDict['queries']="false"
                dataDict['description']="Root Level"
                
            for child in children:
                pVec=None
                with open(os.path.join(inputDir,'embedding_data.txt'),'r') as f:
                    for key,line in enumerate(f):
                        l=line.strip('\n').split(' ')
                        if l[0].strip() == child.strip():
                            pVec=list(np.array(l[1:],dtype=float))
                        else:
                            continue
                ret=self.jsonBuilder(os.path.join(inputDir,child),child,level+1,pVec)
                dataDict['children'].append(ret)                
            return dataDict
        else:
            try:
                dataDict['id']=parent        
                dataDict['name']=parent
                dataDict['center']=parentVec
                dataDict["data"]={"type":"concept","depth":level}
                leaf_nodes=[]
                with open(os.path.join(inputDir,'seed_keywords.txt'),'r') as fin:
                    for line in fin:
                        leaf_dict={}
                        leaf_dict["id"]=line.strip()
                        leaf_dict["data"]={"type":"concept","depth":level}
                        leaf_dict["name"]=line.strip()
                        leaf_dict['center']=None
                        leaf_dict["children"]=[]
                        leaf_nodes.append(leaf_dict)

                with open(os.path.join(inputDir,'doc_ids.txt'),'r') as fin:
                    for line in fin:
                        line = line.strip()
                        if (len(line) == 0):
                            continue
                        line = int(line)
                        if not line in JsonBuild.papers_idx_in_raw:
                            print('[Error] extraction of the original paper failed! (path={0}, doc_idx={1})'.format(inputDir, line))
                            continue
                        if line >= len(JsonBuild.raw_papers):
                            print('[Error] extraction of the original paper out of range! (path={0}, doc_idx={1})'.format(inputDir, line))
                            continue
                        leaf_dict={}
                        paper = JsonBuild.raw_papers[JsonBuild.papers_idx_in_raw[line]]
                        leaf_dict["id"]="__"+paper+"__"
                        leaf_dict["data"]={"type":"papers","depth":level}
                        leaf_dict["name"]=leaf_dict["id"]
                        leaf_dict['center']=None
                        leaf_dict["children"]=[]
                        leaf_nodes.append(leaf_dict)
                dataDict['children']=leaf_nodes
                return dataDict

            except Exception as err:
                print('[Error]:'+ str(err))
                return
            
    def process(self,path,parent='*',level=1):
        try:
            print('mylog: inside JsonBuild.process')
            print('[Info2]: #keys in JsonBuild.papers_idx_in_raw={0}, #raw papers={1}'.format(len(JsonBuild.papers_idx_in_raw), len(JsonBuild.raw_papers)))
            print('mylog2: -1 exists in JsonBuild.papers_idx_in_raw = {0}'.format((-1 in JsonBuild.papers_idx_in_raw)))

            self.dataDict=self.jsonBuilder(path,parent,level)
            self.__rootToLeafPath(self.dataDict)            
        except Exception as err:
            print('[Error] Error in json file generation - check the logs for details')
            print(str(err))
            sys.exit(1)