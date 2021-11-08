import os
import subprocess
import magic

def generate_keystore(keystore, alias):

    CMD = ['keytool', '-genkey', '-v', '-keystore', keystore, '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-alias', alias]
    subprocess.call(CMD)

def zipalign(input_apk, output_apk):
    CMD = ['zipalign', '-p', '4', input_apk, output_apk]
    subprocess.call(CMD)

def verfiy_alignment(apk_file):
    CMD = ['zipalign', '-c', '4', apk_file]
    subprocess.call(CMD)

def sign_with_gplay(apk_file, output_file):
    #output_file = apk_file[:-4] + '_resign' + apk_file[-4:]
    #if store_folder is not None:
    #    output_file = os.path.join(store_folder, output_file)

    CMD = ['java', '-jar', 'tools/signapk.jar', 'tools/testkey.x509.pem', 'tools/testkey.pk8', apk_file, output_file]
    subprocess.call(CMD)


def sign_apk(apk_file, keystore, alias, output_file=None, version='old', password='weaken'):
    '''
    If the version of build-tools is 24.0.2 or older, use the OLD_CMD. Otherwise use NEW_CMD
    '''
    #if output_file is None:
    #    output_file = apk_file[:-4] + '_signed' + apk_file[-4:]
    if version == 'new':
        CMD = ['apksigner', 'sign', '--ks', keystore, apk_file, '--ks-key-alias', alias, '--out', output_file]
    else:
        CMD = ['/usr/bin/jarsigner',
            '-verbose',
            '-sigalg',
            'SHA1withRSA',
            '-digestalg',
            'SHA1',
            '-keystore',
            keystore,
            apk_file,
            alias]
        if output_file is not None:
            CMD.append('-signedjar')
            CMD.append(output_file)

    read, write = os.pipe()
    os.write(write, b'weaken')
    os.close(write)
    subprocess.call(CMD, stdin=read)

def decompile(apk, folder):
    '''
    Decompile apk with ApkTool
    '''
    CMD = ['apktool', 'd', '-o', folder, apk]
    print(CMD)
    subprocess.call(CMD)

def repackage(apk, folder):
    '''
    Repackage the apk for a specific folder
    There are some issues for compilation
    1. libpng cannot parse images that are actually not png file
    workaround: rename the png file to specific pic, like jpg
    '''
    for f in os.listdir(os.path.join(folder, 'res')):
        if f.startswith('drawable') and os.path.isdir(os.path.join(folder, 'res', f)):
            for drawable in os.listdir(os.path.join(folder, 'res', f)):
                if drawable.endswith('.png') or drawable.endswith('.PNG'):
                    file_type = magic.from_file(os.path.join(folder, 'res', f, drawable))
                    if file_type.startswith('JPEG'):
                        os.rename(os.path.join(folder, 'res', f, drawable), os.path.join(folder, 'res', f, drawable[:-3]+'jpg'))
                    elif file_type.startswith('PC bitmap'):
                        os.rename(os.path.join(folder, 'res', f, drawable), os.path.join(folder, 'res', f, drawable[:-3]+'bmp'))
    CMD = ['apktool', 'b', '-o', apk, folder]
    subprocess.call(CMD)
