#!/bin/bash
import os
import sys
sys.path.append('../utils')
import apk_cmd
import shutil
import random
import multiprocessing
sys.path.append('../virustotal/python')

def main(apk_folder, output_folder):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    for root, dirs, files in os.walk(apk_folder):
        for f in files:
            if f[-4:].lower() == '.apk' and not os.path.exists(os.path.join(output_folder, f)):
                apk_cmd.sign_apk(os.path.join(root, f), 'my.keystore', 'resign', output_file=os.path.join(output_folder, f))

'''
Read 1000 malware samples and benign apps from the folder
'''
def main2(apk_folder, output_folder):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    drebin = [item.strip() for item in open('drebin_1000').readlines()]
    benign = [item.strip() for item in open('zero_1000').readlines()]
    grayware = [item.strip() for item in open('grayware_1000').readlines()]

    #pool = multiprocessing.Pool(multiprocessing.cpu_count())
    #pool = multiprocessing.Pool(50)  #Do not occupy all CPUs
    cnt = 0
    for d in drebin:
        apk = os.path.join(apk_folder, d+'_unsign.apk')
        if os.path.exists(apk):
            #apk_cmd.sign_apk(os.path.join(apk_folder, apk), 'my.keystore', 'weaken', os.path.join(output_folder, d+'_resign_mykey.apk'), 'old')
            dest_apk = os.path.join(output_folder, d+'_resign_mykey.apk')
            if not os.path.exists(dest_apk):
                shutil.copyfile(os.path.join(apk_folder, apk), dest_apk)
            cnt += 1
        if cnt == 1000:
            break

    cnt = 0
    for d in benign:
        apk = os.path.join(apk_folder, d+'_unsign.apk')
        if os.path.exists(apk):
            dest_apk = os.path.join(output_folder, d+'_resign_mykey.apk')
            if not os.path.exists(dest_apk):
                shutil.copyfile(os.path.join(apk_folder, apk), dest_apk)
            #apk_cmd.sign_apk(os.path.join(apk_folder, apk), 'my.keystore', 'weaken', os.path.join(output_folder, d+'_resign_mykey.apk'), 'old')
            cnt += 1
        if cnt == 1000:
            break

    cnt = 0
    for d in grayware:
        apk = os.path.join(apk_folder, d+'_unsign.apk')
        if os.path.exists(apk):
            dest_apk = os.path.join(output_folder, d+'_resign_mykey.apk')
            if not os.path.exists(dest_apk):
                shutil.copyfile(os.path.join(apk_folder, apk), dest_apk)
            #apk_cmd.sign_apk(os.path.join(apk_folder, apk), 'my.keystore', 'weaken', os.path.join(output_folder, d+'_resign_mykey.apk'), 'old')
            cnt += 1
        if cnt == 1000:
            break

    for f in os.listdir(output_folder):
        apk_cmd.sign_apk(os.path.join(output_folder, f), 'my.keystore', 'weaken', None, 'old')

    #pool.close()
    #pool.join()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        os.exit('Usage: python resigning.py APK_FOLDER OUTPUT_FOLDER')
    main(sys.argv[1].strip(), sys.argv[2].strip())
