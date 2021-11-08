import os
import sys
import random
import backdoor
import multiprocessing

APP_FOLDER = '/home/data/XXX/exp_apps/fusion'

MALWARE_FOLDER = os.path.join(APP_FOLDER, 'malware')
GRAYWARE_FOLDER = os.path.join(APP_FOLDER, 'grayware')
BENIGN_FOLDER = os.path.join(APP_FOLDER, 'benign')
ANVA_FOLDER = os.path.join(APP_FOLDER, 'anva')

def main():
    malware_list = [os.path.join(MALWARE_FOLDER, f) for f in os.listdir(MALWARE_FOLDER) if f[-4:].lower() == '.apk']
    grayware_list = [os.path.join(GRAYWARE_FOLDER, f) for f in os.listdir(GRAYWARE_FOLDER) if f[-4:].lower() == '.apk']
    benign_list = [os.path.join(BENIGN_FOLDER, f) for f in os.listdir(BENIGN_FOLDER) if f[-4:].lower() == '.apk']
    anva_list = [os.path.join(ANVA_FOLDER, f) for f in os.listdir(ANVA_FOLDER) if f[-4:].lower() == '.apk']

    random.shuffle(malware_list)
    random.shuffle(grayware_list)
    random.shuffle(benign_list)
    random.shuffle(anva_list)

    pool = multiprocessing.Pool(processes=20)
    NUM = 3000
    '''
    Malware and malware
    '''
    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'malware_malware')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        samples = random.sample(malware_list, 2)
        #backdoor.main(samples[0], samples[1], os.path.join(APP_FOLDER, 'malware_malware'))
        pool.apply_async(backdoor.main, (samples[0], samples[1], os.path.join(APP_FOLDER, 'malware_malware'),))
    '''
    Malware and grayware
    '''
    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'malware_grayware')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        malware = malware_list[random.randint(0, len(malware_list)-1)]
        grayware = grayware_list[random.randint(0, len(grayware_list)-1)]
        #backdoor.main(malware, grayware, os.path.join(APP_FOLDER, 'malware_grayware'))
        pool.apply_async(backdoor.main, (malware, grayware, os.path.join(APP_FOLDER, 'malware_grayware'),))
    '''
    Malware and ANVA
    '''
    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'malware_anva')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        malware = malware_list[random.randint(0, len(malware_list)-1)]
        anva = anva_list[random.randint(0, len(anva_list)-1)]
        #backdoor.main(malware, anva, os.path.join(APP_FOLDER, 'malware_anva'))
        pool.apply_async(backdoor.main, (malware, anva, os.path.join(APP_FOLDER, 'malware_anva'),))
    '''
    Malware and benign
    '''
    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'malware_benign')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        malware = malware_list[random.randint(0, len(malware_list)-1)]
        benign = benign_list[random.randint(0, len(benign_list)-1)]
        #backdoor.main(malware, benign, os.path.join(APP_FOLDER, 'malware_benign'))
        pool.apply_async(backdoor.main, (malware, benign, os.path.join(APP_FOLDER, 'malware_benign'),))
    '''
    Grayware and grayware
    '''
    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'grayware_grayware')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        samples = random.sample(grayware_list, 2)
        #backdoor.main(samples[0], samples[1], os.path.join(APP_FOLDER, 'grayware_grayware'))
        pool.apply_async(backdoor.main, (samples[0], samples[1], os.path.join(APP_FOLDER, 'grayware_grayware'),))
    '''
    Grayware and benign
    '''

    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'grayware_benign')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        grayware = grayware_list[random.randint(0, len(grayware_list)-1)]
        benign = benign_list[random.randint(0, len(benign_list)-1)]
        #backdoor.main(grayware, benign, os.path.join(APP_FOLDER, 'grayware_benign'))
        pool.apply_async(backdoor.main, (grayware, benign, os.path.join(APP_FOLDER, 'grayware_benign'),))
    '''
    Grayware and ANVA
    '''

    exists = len([item for item in os.listdir(os.path.join(APP_FOLDER, 'grayware_anva')) if item[-4:] == '.apk'])
    for i in range(0, 3000-exists):
        grayware = grayware_list[random.randint(0, len(grayware_list)-1)]
        anva = anva_list[random.randint(0, len(anva_list)-1)]
        #backdoor.main(grayware, anva, os.path.join(APP_FOLDER, 'grayware_anva'))
        pool.apply_async(backdoor.main, (grayware, anva, os.path.join(APP_FOLDER, 'grayware_anva'),))

    pool.close()
    pool.join()

if __name__ == '__main__':
    main()
