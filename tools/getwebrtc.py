import os
import shutil
import sys
from xml.etree.ElementInclude import include

def script_root():
    return os.path.dirname(os.path.realpath(__file__))

def set_env(key, value):
    os.environ[key] = value

def safe_line(bytes):
    if isinstance(bytes, str):
        s = bytes.strip()
        if len(s) == 0:
            return ''
        return s
    try:
        s = bytes.decode('utf-8', 'ignore').strip()
        if len(s) == 0:
            return ''
        return s
    except:
        return ''
def safe_print(bytes):
    str = safe_line(bytes).rstrip()
    if str == '':
        return
    print(str)

def run(cmds, has_output = True, env=None):
    print('run -> [{}]'.format(' '.join(cmds)))
    if env == None:
        env = os.environ
    import subprocess
    proc = subprocess.Popen(' '.join(cmds), stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, shell=True, env=env)
    while True:
        if has_output:
            o = proc.stdout.readline()
            safe_print(o)
        ret = proc.poll()
        if ret is not None:
            if has_output:
                for o in proc.stdout.readlines():
                    safe_print(o)
            return ret

def execdir(dir, cmds, has_output = True, env=None):
    now_pwd = os.getcwd()
    os.chdir(dir)
    ret = run(cmds, has_output, env=env)
    os.chdir(now_pwd)
    return ret

def do(cmds, has_output = True, env=None):
    return execdir('.', cmds, has_output, env=env)

def uplevel_dir_of(path):
    return os.path.dirname(path)

def gitCheckout(url, path, commit='main', branch='main', deep_clone=False):
    shutil.rmtree(path, True)
    now_path = os.getcwd()
    os.makedirs(path)
    os.chdir(path)
    do(['git', 'init'])
    do(['git', 'remote', 'add', 'origin', url])
    if deep_clone:
        fetch_cmds = ['git', 'fetch', 'origin']
    else:
        fetch_cmds = ['git', 'fetch', '--depth', '1', 'origin']
    fetch_cmds.append(commit)
    do(fetch_cmds)
    checkout_cmds = ['git', 'checkout', 'FETCH_HEAD']
    if branch:
        checkout_cmds.append('-b')
        checkout_cmds.append(branch)
    do(checkout_cmds)
    os.chdir(now_path)

scriptRoot = script_root()
toolsRoot = scriptRoot
projRoot = uplevel_dir_of(scriptRoot)
rtcRev = '4758'
nativeRoot = os.path.join(projRoot, 'native_{}'.format(rtcRev))
buildArch = 'x64'
buildConfig = 'release'
build = False
copyHeader = False

# Download depot_tools
depotToolsPath = os.path.join(toolsRoot, 'depot_tools')

# Skip Path
includeSkipPatten = [
    '\\test\\',
    '_test\\',
    'build\\',
    'example\\',
    '\\android\\',
    '\\android_',
    '\\testing\\',
    '\\.git\\',
    '_web_',
    'third_party\\gtest',
    'third_party\\blink',
    'third_party\\libc++',
    'third_party\\perfetto',
    'third_party\\grpc',
    'third_party\\catapult',
    'third_party\\openh264',
    'third_party\\llvm-build',
    'third_party\\breakpad',
    'third_party\\tensorflow-text',
    'third_party\\libvpx',
    'third_party\\ffmpeg',
    'third_party\\nasm',
    'third_party\\crashpad',
    'third_party\\icu',
    'third_party\\hyphenation-patterns',
    'third_party\\depot_tools',
    'third_party\\protobuf',
    'third_party\\rust',
    'third_party\\tflite_support',
    'third_party\\libaom',
    'sdk\\objc',
    'sdk\\android',
    'tools'
]

def dlDepotTools():
    global depotToolsPath
    if os.path.exists(depotToolsPath) and os.path.isdir(depotToolsPath):
        return
    try:
        gitCheckout(
            'https://chromium.googlesource.com/chromium/tools/depot_tools.git', 
            depotToolsPath,
            commit='main',
            branch='main',
            deep_clone=True
        )
    except:
        os.exit(1)

def dlWebRTC():
    global nativeRoot
    global rtcRev
    srcPath = os.path.join(nativeRoot, 'src')
    if os.path.exists(srcPath) and os.path.isdir(srcPath):
        return
    now_path = os.getcwd()
    try:
        gitCheckout(
            'https://webrtc.googlesource.com/src.git',
            srcPath,
            commit='branch-heads/{}'.format(rtcRev),
            branch='m{}'.format(rtcRev),
            deep_clone=False
        )
        os.chdir(nativeRoot)
    except:
        os.exit(2)
    os.chdir(now_path)

def syncWebRTC():
    global nativeRoot
    gclientConfigPath = os.path.join(nativeRoot, '.gclient')
    if os.path.exists(gclientConfigPath):
        return
    now_path = os.getcwd()
    os.chdir(nativeRoot)
    try:
        with open('.gclient', 'w+') as gclient:
            gclient.writelines([
                'solutions = [\n',
                '  {\n',
                '    "name": "src",\n',
                '    "url": "https://webrtc.googlesource.com/src.git",\n',
                '    "deps_file": "DEPS",\n',
                '    "managed": False,\n',
                '    "custom_deps": {},\n',
                '  },\n',
                ']\n'
            ])
        do(['gclient', 'sync', '--no-history'])
    except:
        os.exit(3)
    os.chdir(now_path)

def buildWebRTC(arch, config):
    global nativeRoot
    global projRoot
    srcPath = os.path.join(nativeRoot, 'src')
    now_path = os.getcwd()
    os.chdir(srcPath)
    build_success = False
    args = [
        'target_os=\\"win\\"',
        'target_cpu=\\"{}\\"'.format(arch),
        'is_debug={}'.format('true' if config == 'debug' else 'false'),
        'is_component_build=false',
        'treat_warnings_as_errors=false',
        'rtc_include_tests=false',
        'rtc_build_examples=false',
        'use_rtti=false',
        'enable_iterator_debugging=true',
        'symbol_level=0',
        'rtc_enable_protobuf=false',
        'rtc_enable_sctp=false',
        'enable_google_benchmarks=false',
        'enable_paint_preview=false',
        'libyuv_include_tests=false',
        'rtc_build_json=false',
        'rtc_build_tools=false',
        'enable_libaom=true',
        'enable_libaom_decoder=true',
        'proprietary_codecs=true',
        'rtc_enable_symbol_export=true',
        'rtc_enable_objc_symbol_export=true',
        'rtc_libvpx_build_vp9=true',
        'rtc_enable_win_wgc=true'
    ]
    try:
        do(['gn', 'gen', '../build_{}_{}'.format(arch, config), '--ide=vs', '--args=\"{}\"'.format(' '.join(args))])
        # do(['gn', 'args', '../build_{}_{}'.format(arch, config), '--list'])
        # os.system('gn args ../build_{}_{} --list'.format(arch, config))
        build_success = (do(['ninja', '-C', '../build_{}_{}'.format(arch, config)]) == 0)
    except:
        os.exit(4)
    os.chdir(now_path)
    
    if build_success:
        libPath = os.path.join(projRoot, 'lib')
        libConfigPath = os.path.join(libPath, arch, config)
        if not os.path.exists(libConfigPath):
            os.makedirs(libConfigPath)
        libWebRTCPath = os.path.join(libConfigPath, 'webrtc.lib')
        if os.path.exists(libWebRTCPath):
            os.remove(libWebRTCPath)
        buildPath = os.path.join(nativeRoot, 'build_{}_{}'.format(arch, config))
        targetPath = os.path.join(buildPath, 'obj', 'webrtc.lib')
        shutil.copy2(targetPath, libWebRTCPath)

def isPathInIgnoreList(path):
    global includeSkipPatten
    for patten in includeSkipPatten:
        if patten in path:
            return True
    return False

def createIncludeDirectory(dir: str):
    global nativeRoot
    global projRoot
    srcPath = os.path.join(nativeRoot, 'src')
    incPath = os.path.join(projRoot, 'include')
    targetPath = os.path.join(incPath, dir.removeprefix(srcPath + '\\'))
    if not os.path.exists(targetPath):
        os.makedirs(targetPath)
    return targetPath

def scanSourceDir(srcPath):
    for path, dirs, files in os.walk(srcPath):
        for f in files:
            split_tup = os.path.splitext(f)
            if split_tup[1] == '.h':
                targetPath = createIncludeDirectory(path)
                print('copy header: {}'.format(os.path.join(path, f)))
                shutil.copy2(os.path.join(path, f), os.path.join(targetPath, f))

        for d in dirs:
            if d[0] == '.':
                continue
            if isPathInIgnoreList(os.path.join(path, d) + '\\'):
                continue
            scanSourceDir(os.path.join(path, d))

def copyHeaders():
    global nativeRoot
    global rtcRev
    global projRoot

    incDir = os.path.join(projRoot, 'include')
    revFile = os.path.join(incDir, '.rtcrev')
    if os.path.exists(incDir):
        if os.path.exists(revFile):
            with open(revFile, 'r') as rf:
                rev = rf.read()
            # Do not need to copy header files as they already existed
            if rev == str(rtcRev):
                return
        shutil.rmtree(incDir, ignore_errors=True)
    if os.path.exists(incDir):
        print('include folder already existed and cannot be removed')
        os.exit(2)
    os.makedirs(incDir)

    srcPath = os.path.join(nativeRoot, 'src')
    scanSourceDir(srcPath)
    # After scan done, write the rev info
    with open(revFile, 'w+') as rf:
        rf.write(str(rtcRev))

for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if not arg.startswith('--'):
        print('invalidate argument: {}'.format(arg))
        os.exit(1)
    kv = arg[2:].split('=')
    arg_key = kv[0]
    if arg_key == 'rev':
        rtcRev = kv[1]
    elif arg_key == 'arch':
        buildArch = kv[1]
    elif arg_key == 'config':
        buildConfig = kv[1].lower()
    elif arg_key == 'build':
        build = True
    elif arg_key == 'copy-header':
        copyHeader = True
    else:
        print('invalidate argument: {}'.format(kv[0]))
        os.exit(1)

nativeRoot = os.path.join(projRoot, 'native_{}'.format(rtcRev))

def kill_child_processes(*args):
    import psutil
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        os.kill(child.pid, signal.SIGKILL)

import atexit
import signal

atexit.register(kill_child_processes)
signal.signal(signal.SIGTERM, kill_child_processes)
signal.signal(signal.SIGINT, kill_child_processes)

# Do downloading
dlDepotTools()

# Set Depot tools and msvc env
set_env('PATH', '{};{}'.format(depotToolsPath, os.environ['PATH']))
set_env('GYP_GENERATORS', 'msvs-ninja,ninja')
set_env('DEPOT_TOOLS_WIN_TOOLCHAIN', '0')
set_env('GYP_MSVS_VERSION', '2019')
set_env('vs2019_install', 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community')
set_env('GYP_MSVS_OVERRIDE_PATH', 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community')

dlWebRTC()
syncWebRTC()

if copyHeader:
    copyHeaders()
if build:
    buildWebRTC(buildArch, buildConfig)
