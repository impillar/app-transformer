#!/bin/bash
import os
import sys
sys.path.append('../utils')
import apk_cmd
import shutil
import random
import multiprocessing

def unsigning(apk_file, out_file):

    apk_cmd.decompile(apk_file, apk_file[:-4])
    apk_cmd.repackage(out_file, apk_file[:-4])
    shutil.rmtree(apk_file[:-4])

    #try:
    #    apk_cmd.decompile(apk_file, apk_file[:-4])
    #    apk_cmd.repackage(out_file, apk_file[:-4])
    #    shutil.rmtree(apk_file[:-4])
    #except:
    #    print('Error encountered when processing ' + apk_file)

def main(apk_folder, output_folder):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    #pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool = multiprocessing.Pool(50)  #Do not occupy all CPUs
    for root, dirs, files in os.walk(apk_folder):
        random.shuffle(files)
        for f in files:
            if f[-4:].lower() == '.apk' and not os.path.exists(os.path.join(output_folder, f[:-4]+'_unsign.apk')):
                #unsigning(os.path.join(root, f), os.path.join(output_folder, f[:-4]+'_unsign.apk'))
                pool.apply_async(unsigning, (os.path.join(root, f), os.path.join(output_folder, f[:-4]+'_unsign.apk'), ))
    pool.close()
    pool.join()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        os.exit('Usage: python unsigning.py APK_FOLDER OUTPUT_FOLDER')
    main(sys.argv[1].strip(), sys.argv[2].strip())
