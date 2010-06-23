# The following version determination code is a greatly simplified version
# of the mercurial repo code. The version is stored in nml/__version__.py
# get_numeric_version is used only for the purpose of packet creation,
# in all other cases use get_version()

import subprocess, os, string, sys

def write_version_file(path, version):
    if version:
        try:
            f = open(os.path.join(path,"nml/__version__.py"), "w")
            f.write('# this file is autogenerated by setup.py\n')
            f.write('version = "%s"\n' % version)
            f.close()
        except IOError:
            print "Version file NOT written"

def get_hg_version(path):
    version = ''
    if os.path.isdir(os.path.join(path,'.hg')):
        # we want to return to where we were. So save the old path
        version_list = (subprocess.Popen(['hg', '-R', path, 'id', '-n', '-t', '-i'], stdout=subprocess.PIPE).communicate()[0]).split()
        if version_list[1].endswith('+'):
            modified = 'M'
        else:
            modified = ''
        revision = string.rstrip(version_list[1],'+')
        hash = string.rstrip(version_list[0],'+')
        # Test whether we have a tag (=release version)
        if version_list[2] != 'tip':
            version = version_list[1] + modified
        else: # we have a trunk version
            version = 'r'+revision + modified + ' (' + hash + ')'
#        print "HG repository with version found: %s" % version
        write_version_file(path, version)
    return version

def get_version():
    # first try whether we find an nml repository. Use that version, if available
    binary_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    version = get_hg_version(binary_path)
    if version:
        return version
    # no repository was found. Return the version which was saved upon built
    try:
        from nml import __version__
        version = __version__.version
    except ImportError:
        version = 'unknown'
    return version

def get_numeric_version():
    return (get_version().split())[0]
