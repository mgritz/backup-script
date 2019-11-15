#!/usr/bin/python

import subprocess
import argparse
import json

def syscmd(cmd, encoding=''):
    '''
    Executes a shell command and returns a tuple of return value
    and shell output.
    Derived from https://stackoverflow.com/questions/5596911/python-os-system-without-the-output
    '''
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        close_fds=True)
    p.wait()
    output = p.stdout.read()
    if len(output) > 1 and encoding:
        output = output.decode(encoding)
    return (p.returncode, output)


class OffSiteConnect:
    def __init__(self, sshLogin):
        self._login = sshLogin
        self._address = self._login.split('@')[-1]

        # try to reach target node for now.
        (rc, out) = syscmd('ping {} -c 1'.format(self._address))

        if rc != 0:
            print('Cannot reach {}, ping returned {}. Aborting.'.format(self._address, rc))
            exit(1)

    def rsyncProbeDifferences(self, sourceTargetMap, excludes):
        '''
        For the given map of sources to targets return the number of files that
        exist on both sides but are different.
        '''
        retval = dict()
        for src, tgt in sourceTargetMap:
            (rc, output) = syscmd('rsync -rins --existing --exclude={} {} {}:{}'.format(excludes, src, self._login, tgt))
            if rc != 0:
                print(output)
                print('Warning: cannot evaluate differences between {} and {}:{}',format(src, self._login, tgt))
                continue
            retval[src] = len(output)
        return retval

    def rsyncUpdateRemote(self, sourceTargetMap, excludes):
        '''
        For the given map of sources to targets update the remote files using rsync.
        '''
        for src, tgt in sourceTargetMap:
            (rc, output) = syscmd('rsync -arP --exclude={} {} {}:{}'.format(excludes, src, self._login, tgt))
            print(output)
            if rc != 0:
                print('Warning: cannot rsync from {} to {}:{}',format(src, self._login, tgt))

########
ap = argparse.ArgumentParser()
ap.add_argument('-c', '--connection', required=True, help='ssh-like connection info, user@address.')
ap.add_argument('-f', '--configfile', required=True, help='JSON-file with configuration')
args = ap.parse_args()

osc = OffSiteConnect(args.connection)

configfile=json.load(args.configfile)
diffs = osc.rsyncProbeDifferences(configfile, None)