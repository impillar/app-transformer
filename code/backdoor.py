#!/usr/bin/python
import os
import sys
import xml.etree.ElementTree as ET
sys.path.append('../utils')
import apk_cmd
#from ..utils import cmd
import shutil
import subprocess

APKTOOL = 'apktool'

#def disassemble():
#    input_file = raw_input('APK to Backdoor: ').strip()
#    os.system(APKTOOL +' d ' + input_file)

'''
Given the root of an AndroidManifest file, return the name of main activity
'''
def get_main(root):

    package = root.get('package')
    '''
    Find the main activity in the AndroidManifest file
    '''
    maniact = ''
    for child in root:
        if child.tag == "application":
            for comp in child:
                if comp.tag == "activity":
                    main_act = comp
                    for attr in comp:
                        if attr.tag == "intent-filter":
                            act_name = attr.find('action').get('{http://schemas.android.com/apk/res/android}name')
                            # There may be more than one category-tagged item
                            cat_names  = [cat.get('{http://schemas.android.com/apk/res/android}name') for cat in attr.findall('category')]

                            #print(act_name, ','.join(cat_names))
                            if 'android.intent.category.LAUNCHER' in cat_names and act_name == 'android.intent.action.MAIN':
                                maniact = main_act.get('{http://schemas.android.com/apk/res/android}name')
                                if maniact[0] == '.':
                                    maniact = package + maniact
                                return maniact
    return None

def yml_merge(rider_name, host_name, dst):

    try:
        '''
        Just a very lazy implementation, only considering doNotCompress and unknownFiles
        '''
        riders = [f.rstrip() for f in open(rider_name).readlines()]
        hosts = [f.rstrip() for f in open(host_name).readlines()]


        rider_do_not_compress = 0
        while rider_do_not_compress < len(riders) and not riders[rider_do_not_compress].startswith('doNotCompress:'):
            rider_do_not_compress += 1

        host_do_not_compress = 0
        while host_do_not_compress < len(hosts) and not hosts[host_do_not_compress].startswith('doNotCompress:'):
            host_do_not_compress += 1

        rider_is_framework_apk = rider_do_not_compress + 1
        while rider_is_framework_apk < len(riders) and not riders[rider_is_framework_apk].startswith('isFrameworkApk'):
            rider_is_framework_apk += 1

        host_is_framework_apk = host_do_not_compress + 1
        while host_is_framework_apk < len(hosts) and not hosts[host_is_framework_apk].startswith('isFrameworkApk'):
            host_is_framework_apk += 1

        for i in range(rider_do_not_compress, rider_is_framework_apk):
            if riders[i] not in hosts[host_do_not_compress:host_is_framework_apk]:
                hosts.insert(host_is_framework_apk, riders[i])
                host_is_framework_apk += 1

        if host_is_framework_apk - host_do_not_compress == 1:
            hosts[host_do_not_compress] = 'doNotCompress: {}'
        else:
            hosts[host_do_not_compress] = 'doNotCompress:'


        rider_unknown_files = 0
        while rider_unknown_files < len(riders) and not riders[rider_unknown_files].startswith('unknownFiles:'):
            rider_unknown_files += 1
        host_unknown_files = 0
        while host_unknown_files < len(hosts) and not hosts[host_unknown_files].startswith('unknownFiles:'):
            host_unknown_files += 1

        rider_uses_framework = riders.index('usesFramework:')
        host_uses_framework = hosts.index('usesFramework:')

        for i in range(rider_unknown_files, rider_uses_framework):
            if riders[i] not in hosts[host_unknown_files:host_uses_framework]:
                hosts.insert(host_uses_framework, riders[i])
                host_uses_framework += 1

        if host_uses_framework - host_unknown_files == 1:
            hosts[host_unknown_files] = 'unknownFiles: {}'
        else:
            hosts[host_unknown_files] = 'unknownFiles:'

        with open(dst, 'w') as fout:
            for line in hosts:
                fout.write(line+'\n')

        return True
    except Exception as e:
        print('ERROR: ' + str(e))
        return False

def xml_merge(rider_xml, host_xml, dst):
    '''
    https://stuff.mit.edu/afs/sipb/project/android/docs/guide/topics/manifest/manifest-intro.html
    All valid elements are listed as follows:
        <action>                //within component
        <activity>
        <activity-alias>
        <application>
        <category>              //within component
        <data>                  //within component
        <grant-uri-permission>  //within provider
        <instrumentation>
        <intent-filter>         //within component
        <manifest>
        <meta-data>             //within provider
        <permission>
        <permission-group>
        <permission-tree>
        <provider>
        <receiver>
        <service>
        <supports-screens>
        <uses-configuration>
        <uses-feature>
        <uses-library>
        <uses-permission>
        <uses-sdk>
    '''

    #This is the tags which need to be merged
    MERGE_TAGS = ['activity', 'activity-alias', 'instrumentation', 'intent-filter', 'permission', 'permission-group',
            'permission-tree', 'provider', 'receiver', 'service', 'supports-screens', 'uses-configuration',
            'uses-feature', 'uses-library','uses-permission', 'uses-sdk']


    try:
        ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
        tree = ET.ElementTree()
        tree.parse(rider_xml)
        root = tree.getroot()

        host_tree = ET.ElementTree()
        host_tree.parse(host_xml)
        host = host_tree.getroot()

        maniact = get_main(root)
        if maniact is not None:
            print(maniact)

        for child in root:
            if child.tag == 'application':
                for comp in child:
                    name = comp.get('{http://schemas.android.com/apk/res/android}name')
                    if name is None:
                        continue
                    if host.find('.//'+comp.tag+'[@{http://schemas.android.com/apk/res/android}name="'+name+'"]') is None:
                        if name == maniact:
                            '''
                            If the current component is MainActivity, remove intent-filter
                            '''
                            for c in comp:
                                comp.remove(c)
                            #for intent_filter in comp.findall('.//intent-filter/'):
                            #    comp.remove(intent_filter)
                        if name[0] == '.':
                            comp.set('{http://schemas.android.com/apk/res/android}name', '.'.join(maniact.split('.')[:-1])+name)
                        host.find('.//application').insert(0, comp)

            else:
                name = child.get('{http://schemas.android.com/apk/res/android}name')
                if name is None:
                    continue
                if host.find('.//'+child.tag+'[@{http://schemas.android.com/apk/res/android}name="'+name+'"]') is None:
                    host.insert(0, child)
        host_tree.write(dst)
        return True
    except Exception as e:
        print('ERROR: ' + str(e))
        return False

def value_merge(rider_res, host_res, new_res):

    try:
        for d in os.listdir(rider_res):
            if d == 'values' or d.startswith('values-'):
                for f in os.listdir(os.path.join(rider_res, d)):
                    if f[-4:] == '.xml' and os.path.isfile(os.path.join(host_res, d, f)):

                        tree = ET.ElementTree()
                        tree.parse(os.path.join(rider_res, d, f))
                        root = tree.getroot()

                        host_tree = ET.ElementTree()
                        host_tree.parse(os.path.join(host_res, d, f))
                        host = host_tree.getroot()

                        for child in root:
                            name = child.get('name')
                            if name is None:
                                print(os.path.join(rider_res, d, f), )
                                sys.exit(1)
                            tag = child.tag
                            if host.find('.//'+tag+'[@name="'+name+'"]') is None:
                                host.insert(0, child)
                        host_tree.write(os.path.join(new_res, d, f))
        return True
    except Exception as e:
        print('ERROR: ' + str(e))
        return False

def main(rider, host, output_folder, tmp_folder='/home/data/guozhu/AVScale/3429436173_impillar2017/exp_apps/temp'):

    if not os.path.exists(output_folder):
        print('Create the folder', output_folder)
        os.makedirs(output_folder)

    target_apk = os.path.join(output_folder, os.path.basename(host)[:-4]+'_'+os.path.basename(rider)[:-4]+'.apk')
    if os.path.exists(target_apk):
        print('Already done of fusing', os.path.basename(host), 'and', os.path.basename(rider))
        return

    if not os.path.exists(rider[:-4]):
        print('Decompile', rider, 'into', rider[:-4])
        apk_cmd.decompile(rider, rider[:-4])

    if not os.path.exists(host[:-4]):
        print('Decompile', host, 'into', host[:-4])
        apk_cmd.decompile(host, host[:-4])

    '''
    First copy host code, then copy rider code, replace AndroidManifest.xml and apktool.yml
    File structure:
    host[:-4]_rider[:-4]/
    |____code/
    |____host[:-4]_rider[:-4].apk
    |____host[:-4]_rider[:-4]_signed.apk
    '''

    print('Create the folder for the new apk under', os.path.join(tmp_folder, os.path.basename(host)[:-4]+'_'+os.path.basename(rider)[:-4]))
    new_folder = os.path.join(tmp_folder, os.path.basename(host)[:-4]+'_'+os.path.basename(rider)[:-4])

    if not os.path.isdir(os.path.join(new_folder, 'code')):
        os.makedirs(os.path.join(new_folder, 'code'))

    print('cp', '-vr', os.path.join(rider[:-4], '*'), os.path.join(new_folder, 'code'))
    print('cp', '-vr', os.path.join(host[:-4], '*'), os.path.join(new_folder, 'code'))
    #subprocess.call(['cp', '-vr', rider[:-4]+'/*', os.path.join(new_folder, 'code')], shell=True)
    subprocess.call('cp -vr ' + rider[:-4] + '/* ' + new_folder + '/code', shell=True)
    #subprocess.call(['cp', '-vr', host[:-4]+'/*', os.path.join(new_folder, 'code')], shell=True)
    subprocess.call('cp -vr ' + host[:-4] + '/* ' + new_folder + '/code', shell=True)
    #shutil.move(rider[:-4], os.path.join(new_folder, 'code'))
    #shutil.move(host[:-4], os.path.join(new_folder, 'code'))
    #for f in os.listdir(rider[:-4]):
    #    if os.path.isfile(os.path.join(rider[:-4], f)):
    #        shutil.move(os.path.join(rider[:-4], f), os.path.join(new_folder, 'code'))
    #    else:
    #        shutil.move(os.path.join(rider[:-4],f), os.path.join(new_folder, 'code'))

    #for f in os.listdir(host[:-4]):
    #    if os.path.isfile(os.path.join(host[:-4], f)):
    #        shutil.move(os.path.join(host[:-4], f), os.path.join(new_folder, 'code'))
    #    else:
    #        shutil.move(os.path.join(host[:-4],f), os.path.join(new_folder, 'code'))


    print('Merge AndroidManifest and apktool.yml')
    if not xml_merge(os.path.join(rider[:-4], 'AndroidManifest.xml'), os.path.join(host[:-4], 'AndroidManifest.xml'), os.path.join(new_folder, 'code', 'AndroidManifest.xml')):
        return

    if not yml_merge(os.path.join(rider[:-4], 'apktool.yml'), os.path.join(host[:-4], 'apktool.yml'), os.path.join(new_folder, 'code', 'apktool.yml')):
        return

    print('Merge xml files in res/value* folders')
    if not value_merge(os.path.join(rider[:-4], 'res'), os.path.join(host[:-4], 'res'), os.path.join(new_folder, 'code', 'res')):
        return

    #print('Remove the folders ', rider[:-4], 'and', host[:-4])
    #shutil.rmtree(rider[:-4])
    #shutil.rmtree(host[:-4])

    '''
    Delete public.xml because there probably has a conflicting error like
    ************************************************************************************
    W: /.../res/values/public.xml:5084: error: Public resource style/Base.V26.Widget.AppCompat.Toolbar has conflicting type codes for its public identifiers (0x6 vs 0x13).
    ************************************************************************************
    https://blog.csdn.net/Ueming/article/details/101542956
    '''
    os.remove(os.path.join(new_folder, 'code', 'res', 'values', 'public.xml'))

    '''
    Create a keystore if not exist
    '''
    if not os.path.isfile('my.keystore'):
        apk_cmd.generate_keystore('my.keystore', 'weaken')

    print('Repackage a new apk')
    '''
    Repackage twice if one of them fails
    '''
    apk_cmd.repackage(target_apk, os.path.join(new_folder, 'code'))
    apk_cmd.repackage(target_apk, os.path.join(new_folder, 'code'))
    apk_cmd.sign_apk(target_apk, 'my.keystore', 'fusion', version='old', password='weaken')

if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('Usage: python backdoor.py rider.apk host.apk output_folder')
    if not sys.argv[1].endswith('.apk'):
        sys.exit('Rider apk should be with a .apk suffix')
    if not sys.argv[2].endswith('.apk'):
        sys.exit('Host apk should be with a .apk suffix')
    main(sys.argv[1].strip(), sys.argv[2].strip(), output_folder.strip())

