import os
import sys
import subprocess
import multiprocessing

def packer(apk_path, output_folder):
    cmd = ['java', '-jar', 'Bangcle.jar', 'b', apk_path, output_folder]
    subprocess.call(cmd)

def main(app_folder, output_folder):

    pool = multiprocessing.Pool(processes=50)
    for root, dirs, files in os.walk(app_folder):
        for f in files:
            if f[-4:].lower() == '.apk':
                pool.apply_async(packer, (os.path.join(root, f), output_folder,))
    pool.close()
    pool.join()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        os.exit('Usage: python packer.py APP_FOLDER OUTPUT_FOLDER')
    main(sys.argv[1].strip(), sys.argv[2].strip())
