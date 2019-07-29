'''
'''
import random
import argparse
from datetime import datetime
import pdb
import logging
import os
import json

import numpy as np
import networkx as nx # for manipulating graph data-structure
from ete3 import Tree
try:
    from ete3 import TreeStyle, NodeStyle
except ImportError:
    pass
from sklearn.model_selection import KFold
from tabulate import tabulate

from bhcd import BHCD # install bhcd inplace from ../community_detection/bhcd/

from ic_prediction import info_clustering_prediction
from utility import train_test_split
from evaluation import evaluate_single

LOGGING_FILE = 'nips_authorship.log'
logging.basicConfig(filename=os.path.join('build', LOGGING_FILE), level=logging.INFO, format='%(asctime)s %(message)s')

            
def plot_clustering_tree(tree, alg_name):
    ts = TreeStyle()
    ts.rotation = 90
    ts.show_scale = False
    time_str = datetime.now().strftime('%Y-%m-%d-')    
    tree.render(os.path.join('build', time_str + alg_name + '.pdf'), tree_style=ts)
    
def make_table(dic, tb_name, format='latex_raw'):
    table = [[] for i in range(len(dic.keys()))]
    for index, method_name in enumerate(dic.keys()):
        table[index].append(method_name)
        v = dic[method_name]
        tpr, tnr, acc = v['tpr'], v['tnr'], v['acc']
        table[index].extend(['%.3f\\%%'%(100*tpr), '%.3f\\%%'%(100*tnr), '%.3f\\%%'%(100*acc)])
    _headers = ['Method', 'TPR', 'TNR', 'ACC']
    align_list = ['center' for i in range(len(_headers))]
    table_string = tabulate(table, headers = _headers, tablefmt = format, floatfmt='.3f', colalign=align_list)
        
    if(format == 'latex_raw'):
        table_suffix = '.tex'
    elif(format == 'html'):
        table_suffix = '.html'
        
    with open(os.path.join('build', tb_name + table_suffix),'w') as f: 
        f.write(table_string)

def evaluate_single_wrapper(alg, G):
    new_g, test_edge_list = train_test_split(G)
    return evaluate_single(alg, test_edge_list, new_g)

def evaluate(num_times, method_dic, G):
    '''
        num_times: int
    '''
    report = {
        "tpr": 0,
        "tnr": 0,
        "acc": 0
    }
    for i in range(num_times):
    for alg_name, method in method_dic.items():
        print('running ' + alg_name)
        res = evaluate_single_wrapper(method, G)            
    
    logging.info('eval ' + str(type(alg)) + ' num_times=%d'%(num_times))
      
        res = evaluate_single_wrapper(alg, G)
        logging.info('round {0}: with res = {1}'.format(i, res))
        for k in report:
            report[k] += res[k]
    for k in report:
        report[k] /= num_times
    print('evaluation result for ', alg_name, res)           
        
    return report
        
def save_tree_txt(tree, alg_name):
    tree_txt = tree.write()
    time_str = datetime.now().strftime('%Y-%m-%d-')    
    
    write_file_name = os.path.join('build', time_str + '_' + alg_name + '_tree.nw')
    with open(write_file_name, 'w') as f:
        f.write(tree_txt)

            
if __name__ == '__main__':
    method_chocies = ['info-clustering', 'bhcd', 'all']
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_graph', default=0, type=int, help='whether to save gv file')
    parser.add_argument('--load_graph', help='use custom gml file to initialize the graph')     
    parser.add_argument('--save_tree', default=0, type=int, help='whether to save the clustering tree file after clustering, =0 not save, =1 save original(pdf), =2 save ete format txt')     
    parser.add_argument('--alg', default='all', choices=method_chocies, help='which algorithm to run', nargs='+')
    parser.add_argument('--weight', default='triangle-power', help='for info-clustering method, the edge weight shold be used. This parameters'
        ' specifies how to modify the edge weight.')    
    parser.add_argument('--debug', default=False, type=bool, nargs='?', const=True, help='whether to enter debug mode')                  
    parser.add_argument('--evaluate', default=1, type=int, help='when evaluate=1, evaluate the method once; when evaluate=2, iterate given times; evaluate=0, no evaluation.')
    parser.add_argument('--num_times', default=10, type=int, help='the number of times of evaluation')                      
    parser.add_argument('--seed', default=0, type=int, help='positive integer to seed the numpy random generator')                          
    args = parser.parse_args()
    method_chocies.pop()
    if(args.debug):
        pdb.set_trace()
    if(args.load_graph):
        G = nx.read_gml(os.path.join('build', args.load_graph))
    else:
        G = nx.read_gml(os.path.join('build', 'nips-234.gml'))    
    if(args.save_graph):
        raise NotImplementedError("")
    methods = []
    if(args.alg.count('all') > 0):
        args.alg = method_chocies
    if(args.alg.count('info-clustering') > 0):
        methods.append(info_clustering_prediction())
    if(args.alg.count('bhcd') > 0):
        methods.append(BHCD())
    if(len(methods)==0):
        raise ValueError('unknown algorithm')
    
    if(args.seed > 0):
        np.random.seed(args.seed)
    
    if(args.evaluate == 2):
        print('logging to', LOGGING_FILE)
        tabulate_dic = {}
        for i, method in enumerate(methods):
            report = evaluate(args.num_times, method, G)
            tabulate_dic[args.alg[i]] = report
            logging.info('final report' + json.dumps(report))
        make_table(tabulate_dic, 'compare')
    elif(args.evaluate == 1):
        method_dic = {}
        for i, method in enumerate(methods):
            alg_name = args.alg[i]
            method_dic[alg_name] = method
        evaluate(args.num_times, method_dic, G)
    else:
        for method in methods:
            method.fit(G)
    if(args.save_tree):
        for i, method in enumerate(methods):
            alg_name = args.alg[i]
            if(args.save_tree == 2):
                save_tree_txt(method.tree, alg_name)
            elif(args.save_tree == 1):
                plot_clustering_tree(method.tree, alg_name, args.save_tree)
