#!/bin/bash
import os
import sys
sys.path.append('../utils')
import apk_cmd
import xml.etree.ElementTree as ET
import multiprocessing
import shutil
import magic
import json
MODULE_MANIFEST = 'prune/module.json'

def get_host_class(package):
    '''
    Many smali code is of the format 'xxx$1', indicating it is an inner class for xxx
    '''
    ind = 0
    while ind < len(package) and package[ind] != '$':
        ind += 1
    if ind < len(package):
        return package[:ind] + ';'
    return package

def remove_code(smali_file, output=None, keeps=[]):
    '''
    Remove concrete code in smali file, and overwrite to the original file if 'output' is not specified
    '''
    lines = [line.strip() for line in open(smali_file).readlines()]

    '''
    Partial pruning. If this class is in our keeps list, ignore
    '''
    class_name = get_host_class(lines[0].split(' ')[-1])
    if class_name in keeps:
        print('Keep class {}'.format(lines[0]))
        return

    i = 0
    new_content = []
    while i < len(lines):

        new_content.append(lines[i])

        '''
        1. There are four types of return statements in smali
        return-void         : return a void
        return v_{x}        : return a 32bit value of basic type, i.e., int, float, double, char, long, byte, short, boolean
        return-wide v_{x}   : return a 64bit value of basic type
        return-object v_{x} : return an object

        2. abstract method cannot have a body
        3. native method cannot have a body
        '''
        RETURNS = ['return-void', 'return', 'return-wide', 'return-object']
        if lines[i].startswith('.method'):

            '''
            Check whether the method is abstract
            '''
            is_abstract = 'abstract' in lines[i].strip().split(' ')
            is_native = 'native' in lines[i].strip().split(' ')

            i += 1

            return_type = 'return-void'

            while i < len(lines) and not lines[i].startswith('.end method'):
                if lines[i].strip().split(' ')[0] in RETURNS:
                    return_type = lines[i].strip().split(' ')[0]
                i += 1

            if i < len(lines):
                if not is_abstract and not is_native:
                    if return_type == 'return-void':
                        new_content.append('\t.locals 0')
                        new_content.append('\treturn-void')
                    else:
                        new_content.append('\t.locals 1')
                        new_content.append('\tconst/4 v0, 0x0')
                        new_content.append('\t' + return_type + ' v0')
                new_content.append(lines[i])

        i += 1

    if output is None:
        output = smali_file

    with open(output, 'w') as fout:
        for ct in new_content:
            fout.write(ct+'\n')

def proc_folder(smali_folder, keeps=[]):
    for root, dirs, files in os.walk(smali_folder):
        for name in files:
            if name.endswith('.smali'):
                remove_code(os.path.join(root, name), keeps=keeps)

'''
Remove native code in apk folder
'''
def remove_native(apk_folder):
    for root, dirs, files in os.walk(apk_folder):
        for name in files:
            if name.endswith('.so'):
                #print('Delete ' + os.path.join(root, name))
                os.remove(os.path.join(root, name))
            else:
                m = magic.from_file(os.path.join(root, name))
                if m == 'data' or m.startswith('ELF'):
                    #print('Delete ' + os.path.join(root, name))
                    os.remove(os.path.join(root, name))
                else:
                    '''
                    Cornor case: delete legacy file in malware DroidKungFu1
                    '''
                    if m.startswith('Java') and name == 'legacy':
                        #print('Delete ' + os.path.join(root, name))
                        os.remove(os.path.join(root, name))
    '''
    Delete public.xml to avoid an error of missing files caused by deletion
    public.xml may contain the identifiers for specific data
    '''
    os.remove(os.path.join(apk_folder, 'res/values/public.xml'))

'''
Remove xml elements
'''
def remove_elements(manifest):
    tree = ET.ElementTree()
    tree.parse(manifest)
    root = tree.getroot()
    for child in root:
        if child.tag in ['permission', 'permission-group', 'permission-tree', 'uses-configuration', 'uses-feature', 'uses-library', 'uses-permission', 'uses-sdk']:
            root.remove(child)

    tree.write(manifest)

def prune_perm(apk_file, output_folder):

    target_file = os.path.join(output_folder, os.path.basename(apk_file)[:-4]+'_prune_xml.apk')
    if os.path.exists(target_file):
        return
    try:
        apk_cmd.decompile(apk_file, apk_file[:-4])
        remove_elements(os.path.join(os.path.join(apk_file[:-4], 'AndroidManifest.xml')))
        apk_cmd.repackage(target_file, apk_file[:-4])
        shutil.rmtree(apk_file[:-4])
        apk_cmd.sign_apk(target_file, 'my.keystore', 'weaken', version='old')
    except Exception as e:
        if os.path.exists(apk_file[:-4]):
            shutil.rmtree(apk_file[:-4])
        raise e
        #print('Error encountered for ' + apk_file)

def prune_native(apk_file, output_folder):

    target_file = os.path.join(output_folder, os.path.basename(apk_file)[:-4]+'_prune_native.apk')
    if os.path.exists(target_file):
        return
    try:
        apk_cmd.decompile(apk_file, apk_file[:-4])
        remove_native(os.path.join(apk_file[:-4]))
        apk_cmd.repackage(target_file, apk_file[:-4])
        shutil.rmtree(apk_file[:-4])
        apk_cmd.sign_apk(target_file, 'my.keystore', 'weaken', version='old')
    except Exception as e:
        if os.path.exists(apk_file[:-4]):
            shutil.rmtree(apk_file[:-4])
        raise e
        #print('Error encountered for ' + apk_file)

def prune_smali(apk_file, output_folder, keeps=[]):

    target_file = os.path.join(output_folder, os.path.basename(apk_file)[:-4]+'_prune_smali.apk')
    if os.path.exists(target_file):
        return

    try:
        apk_cmd.decompile(apk_file, apk_file[:-4])
        for dr in os.listdir(apk_file[:-4]):
            #print('directory:', dr, os.path.isdir(dr), dr.startswith('smali'))
            if os.path.isdir(os.path.join(apk_file[:-4], dr)) and dr.startswith('smali'):
                proc_folder(os.path.join(apk_file[:-4], dr), keeps=keeps)
        apk_cmd.repackage(target_file, apk_file[:-4])
        shutil.rmtree(apk_file[:-4])
        apk_cmd.sign_apk(target_file, 'my.keystore', 'weaken', version='old')
    except Exception as e:
        if os.path.exists(apk_file[:-4]):
            shutil.rmtree(apk_file[:-4])
        raise e
        #print('Error encountered for ' + apk_file)

def prune_smali2(apk_file, output_folder, keeps=[]):
    for i in range(0, len(keeps)):
        target_file = os.path.join(output_folder, os.path.basename(apk_file)[:-4]+'_prune_'+str(i)+'.apk')
        if os.path.exists(target_file):
            continue

        print('Generating', target_file)
        try:
            apk_cmd.decompile(apk_file, apk_file[:-4])
            for dr in os.listdir(apk_file[:-4]):
                #print('directory:', dr, os.path.isdir(dr), dr.startswith('smali'))
                if os.path.isdir(os.path.join(apk_file[:-4], dr)) and dr.startswith('smali'):
                    proc_folder(os.path.join(apk_file[:-4], dr), keeps=keeps[i])
            apk_cmd.repackage(target_file, apk_file[:-4])
            shutil.rmtree(apk_file[:-4])
            apk_cmd.sign_apk(target_file, 'my.keystore', 'weaken', version='old')
        except Exception as e:
            if os.path.exists(apk_file[:-4]):
                shutil.rmtree(apk_file[:-4])
            raise e
            #print('Error encountered for ' + apk_file)

def prune(apk_file, output_folder):

    prune_smali(apk_file, output_folder)
    prune_native(apk_file, output_folder)
    prune_perm(apk_file, output_folder)

def main(apk_folder, output_folder):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for root, dirs, files in os.walk(apk_folder):
        for f in files:
            if f[-4:].lower() == '.apk':
                pool.apply_async(prune, (os.path.join(root, f), output_folder, ))
                #prune(os.path.join(root, f), output_folder)
    pool.close()
    pool.join()

def prune_deeper(apk_folder, output_folder):

    '''
    Load remain lists
    '''
    manifest = json.load(open(MODULE_MANIFEST))

    keeps = []
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    #pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool = multiprocessing.Pool(processes=30)
    for root, dirs, files in os.walk(apk_folder):
        for f in files:
            if f[-4:].lower() == '.apk':
                if f[:-4] not in manifest:
                    continue
                pool.apply_async(prune_smali2, (os.path.join(root, f), output_folder, manifest[f[:-4]],))
                #prune(os.path.join(root, f), output_folder)
    pool.close()
    pool.join()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        os.exit('Usage: python prune.py APK_FOLDER OUTPUT_FOLDER')
    #main(sys.argv[1].strip(), sys.argv[2].strip())
    prune_deeper(sys.argv[1].strip(), sys.argv[2].strip())
