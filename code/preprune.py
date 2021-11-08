import os
import sys
import showpng
import json

sys.path.append('/home/XXX/androguard')
#from androguard.core.bytecodes import apk,dvm
#from androguard.core.analysis import analysis

from androguard.misc import AnalyzeAPK

import matplotlib.pyplot as plt
import networkx as nx
import subprocess

import pymysql.cursors
import pymysql
import re

from androguard.core.analysis.analysis import ExternalMethod

APP_FOLDER = '/home/data/XXX/exp_apps/apps_prune_smali_deeper'

dialdroid = '/home/XXX/ic3-dialdroid/build/ic3-android.jar'
android_platform = '/home/data/XXX/Android/Sdk/platforms/'

MODULE_MANIFEST = 'prune/module.json'

config = {
    'host':'10.10.71.67',
    'port':3306,  #MySQL port
    'user':'root',#mysql default user
    'password':'123456789',
    'db':'dialdroid', #database
    'charset':'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,

}

def connect_create(sql):
    con = pymysql.connect(**config)
    try:
        with con.cursor() as cursor:
            ifilterId = 'SELECT intentfilters.id FROM classes,components,intentfilters WHERE  intentfilters.component_id=components.id AND components.class_id=classes.id AND     classes.app_id=(SELECT id FROM applications WHERE app=\'org.arguslab.icc_implicit_data1\')'
            cursor.execute(sql)
            result = cursor.fetchall()
    except Exception as e:
        print(str(e))
    finally:
        con.close()
    return result

def methodRepresent(method):
    if method!='':
        method = method.replace('.','/')
        method = re.split(r'[ <:(\s]\s*',method)
        method = 'L'+method[1]+'; '+method[3]
    return method

def classRepresent(classname):
    if classname!='':
        classname = classname.replace('.','/')
        classname = 'L'+classname+';'
    return classname

def app_info(sha):
    sql = 'select * from applications'
    iccdata = connect_create(sql)
    for item in iccdata:
        print(item)

def app_info2():
    applications = []
    iccs = 'SELECT app,shasum,classes.class, exitpoints.method as source,intentclasses.class as target FROM classes,exitpoints,intents,intentclasses,applications where classes.id=exitpoints.class_id and exitpoints.id=intents.exit_id and intents.id=intentclasses.intent_id and classes.app_id=applications.id'
    iccdata = connect_create(iccs)
    for item in iccdata:
        #print(item)
        info = {}
        app         = item['shasum']
        classname   = '' if item['class']==None else classRepresent(item['class'])
        method = methodRepresent(item['source'])
        target = item['target']
        if target!='(.*)':
            target = 'L'+target.replace('.','/')+';'
        info['sha256'] = app
        info['sourceclass'] = classname
        info['sourceMethod'] = method
        info['targetclass'] = target

        #if app.lower() == sha.lower() or True:
        #    print(classname + '->' + target)
        applications.append(info)
    return applications


def run_ic3_dialdroid(apk_path):
    cmd = 'java -Xms16G -jar {} -input {} -cp {} -db dialdroid'.format(dialdroid, apk_path, android_platform)
    print(cmd)
    subprocess.call(cmd.split(' '))


def is_r_class(package):
    if re.match('.*\/R(\$[^\/]*)?;$', str(package)):
        return True
    return False
    #if package.endswith(b'/R;') or package.endswith(b'/R$style;') or package.endswith(b'/R$string;') or package.endswith(b'/R$attr;') or package.endswith(b'/R$drawable;') or package.endswith(b'/R$layout;') or package.endswith(b'/R$id;') or package.endswith(b'/R$raw;'):
    #    return True

def get_host_class(package):
    '''
    Many smali code is of the format 'xxx$1', indicating it is an inner class for xxx
    Some exception: xxx.yyy.zzz$1$2;
    '''
    ind = 0
    while ind < len(package) and package[ind] != '$':
        ind += 1
    if ind < len(package):
        return package[:ind] + ';'
    return package

    '''
    ind = len(package)-1
    while ind >= 0 and  package[ind] != '$':
        ind -= 1
    if ind >= 0:
        return package[:ind] + ';'
    return package
    '''


def filter(mtd):
    return mtd.is_android_api() or is_r_class(mtd.get_class_name())

def modularize(sha256, apk_path, records):
    #app = apk.APK(apk_path)
    #d = dvm.DalvikVMFormat(app.get_dex())
    #dx = analysis.Analysis(d)
    a, d, dx = AnalyzeAPK(apk_path)
    cg = dx.get_call_graph()


    sim_cg = nx.Graph()
    for u, v in cg.edges():
        u_class = get_host_class(u.get_class_name())
        v_class = get_host_class(v.get_class_name())
        if filter(u) and filter(v):
            continue
        if filter(u):
            sim_cg.add_node(v_class)
            continue
        if filter(v):
            sim_cg.add_node(u_class)
            continue
        #u_class = u.get_class_name()
        #v_class = v.get_class_name()
        if u_class not in sim_cg.nodes:
            sim_cg.add_node(u_class)
        if v_class not in sim_cg.nodes:
            sim_cg.add_node(v_class)

        if not sim_cg.has_edge(u_class, v_class) and u_class != v_class:
            sim_cg.add_edge(u_class, v_class)

    node_num = 0
    edge_num = 0
    for item in records:
        if item['sha256'].lower() == sha256.lower():
            source = get_host_class(item['sourceclass'])
            target = get_host_class(item['targetclass'])
            if '$' in source or '$' in target:
                print(source, target)
                return
            if source not in sim_cg.nodes:
                sim_cg.add_node(source)
                node_num += 1
            if target not in sim_cg.nodes:
                sim_cg.add_node(target)
                node_num += 1
            if not sim_cg.has_edge(source, target) and source != target:
                sim_cg.add_edge(source, target)
                edge_num += 1
    print('Add {} nodes and {} edges'.format(node_num, edge_num))

    '''
    for m in dx.find_methods(classname=".*"):
        orig_method = m.get_method()
        # print("Found Method --> {}".format(orig_method))
        # orig_method might be a ExternalMethod too...
        # so you can check it here also:
        if isinstance(orig_method, ExternalMethod):
            is_this_external = True
            # If this class is external, there will be very likely
            # no xref_to stored! If there is, it is probably a bug in androguard...
        else:
            is_this_external = False

        CFG.add_node(orig_method, external=is_this_external)

        for other_class, callee, offset in m.get_xref_to():
            #print(m, callee)
            if isinstance(callee, ExternalMethod):
                is_external = True
            else:
                is_external = False

            callee = callee.get_class_name()
            if callee not in CFG.nodes:
                CFG.add_node(callee)

                # As this is a DiGraph and we are not interested in duplicate edges,
                # check if the edge is already in the edge set.
                # If you need all calls, you probably want to check out MultiDiGraph
            if not CFG.has_edge(orig_method.get_class_name(), callee):
                CFG.add_edge(orig_method.get_class_name(), callee)
    pos = nx.spring_layout(CFG)
    internal = []
    external = []

    print('Nodes: {}, Edges: {}'.format(CFG.number_of_nodes(), CFG.number_of_edges()))
    for n in CFG.nodes:
        if isinstance(n, ExternalMethod):
            external.append(n)
        else:
            internal.append(n)
    '''

    #print('Nodes: {}, Edges: {}'.format(sim_cg.number_of_nodes(), sim_cg.number_of_edges()))
    clusters = []
    for u in sim_cg.nodes():
        found = False
        for cluster in clusters:
            for ele in cluster:
                if sim_cg.has_edge(u, ele):
                    cluster.append(str(u))
                    found = True
                    break
            if found:
                break
        if not found:
            clusters.append([str(u)])

    #for cluster in clusters:
    #    for cl in cluster:
    #        cl = str(cl)
    #        print(cl, type(cl))

    for cluster in clusters:
        print(cluster)

    #print('len: {}'.format(len(clusters)))
    #pos = nx.spring_layout(sim_cg, iterations=500)
    print('Nodes: {}, Edges: {}, Clusters: {}'.format(sim_cg.number_of_nodes(), sim_cg.number_of_edges(), len(clusters)))
    with open('prune/stat.csv', 'a') as fout:
        fout.write('{}, {}, {}, {}\n'.format(sha256, sim_cg.number_of_nodes(), sim_cg.number_of_edges(), len(clusters)))
    return

    #nx.draw(sim_cg, pos=pos, with_labels=True)
    #plt.draw()

    try:
        root = json.load(open(MODULE_MANIFEST))
    except:
        root = dict()

    if sha256 not in root:
        root[sha256] = clusters
    json.dump(root, open(MODULE_MANIFEST, 'w'), indent=4, ensure_ascii=True)

    '''
    plt.show()
    #app_info(os.path.basename(apk_path)[:-4])

    print('Nodes: {}, Edges: {}'.format(cg.number_of_nodes(), cg.number_of_edges()))
    cg = nx.Graph(cg)
    sim_cg = nx.Graph()


    for u in cg.nodes():
        class_name = get_host_class(u.get_class_name())
        if is_r_class(class_name):
            continue
        sim_cg.add_node(class_name)

    for u, v in cg.edges():
        u_class = get_host_class(u.get_class_name())
        v_class = get_host_class(v.get_class_name())
        if is_r_class(u_class) or is_r_class(v_class):
            continue
        #print(u.get_class_name() + '->' + v.get_class_name())
        sim_cg.add_edge(u.get_class_name(), v.get_class_name())
    print('Nodes: {}, Edges: {}'.format(sim_cg.number_of_nodes(), sim_cg.number_of_edges()))
    options = {
        'node_color': 'blue',
        'node_size': 100,
        'width': 3,
    }

    nx.draw(sim_cg, with_labels=True)
    '''
    #plt.savefig('tmp/test.png')
    #showpng.show('tmp/test.png')

def run_icc():
    for f in os.listdir(APP_FOLDER):
        run_ic3_dialdroid(os.path.join(APP_FOLDER, f))

def run_callgraph():
    cnt = 0
    records = app_info2()
    for f in os.listdir(APP_FOLDER):
        #if cnt != 11:
        #    cnt+= 1
        #    continue
        modularize(f[:-4], os.path.join(APP_FOLDER, f), records)
        #break

if __name__ == '__main__':
    #run_icc()
    #main()
    run_callgraph()
    #app_info2('5C4A29D86B72F53F69C09B87E20CBAC3E92F2C6014D727DFA6870DBBB5528516')
