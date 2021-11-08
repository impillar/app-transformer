#!/bin/bash
import os
import sys
sys.path.append('../utils')
import apk_cmd
import shutil
import random
import multiprocessing

def main(apk_folder, output_folder):

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    #pool = multiprocessing.Pool(multiprocessing.cpu_count())
    #pool = multiprocessing.Pool(50)  #Do not occupy all CPUs
    for root, dirs, files in os.walk(apk_folder):
        random.shuffle(files)
        for f in files:
            if f[-4:].lower() == '.apk':
                output_file = os.path.join(output_folder, f[:-4]+'_resign.apk')
                if not os.path.exists(output_file):
                    apk_cmd.sign_with_gplay(os.path.join(root, f), output_file)
                    #pool.apply_async(apk_cmd.sign_with_gplay, (os.path.join(root, f), output_file, ))
    #pool.close()
    #pool.join()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        os.exit('Usage: python resigning.py APK_FOLDER OUTPUT_FOLDER')
    main(sys.argv[1].strip(), sys.argv[2].strip())
