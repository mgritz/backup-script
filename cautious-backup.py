#!/usr/bin/python

import subprocess
import argparse
import json


def syscmd(cmd, encoding='', showOutput=False):
    '''
    Executes a shell command and returns a tuple of return value
    and shell output.
    Derived from https://stackoverflow.com/questions/5596911/python-os-system-without-the-output
    '''
    print('Issuing command $ {}'.format(cmd))
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         close_fds=True)
    p.wait()
    output = p.stdout.read()
    if showOutput:
        print(output)
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
            print('Cannot reach {}, ping returned {}. Aborting.'.format(
                self._address, rc))
            exit(1)

    def _exclRsyncStr(self, excludes):
        '''
        Transfor an array of exclude files into an rsync-compatible exclude
        string like "--exclude=/foo --exclude=/bar/baz" and so on.
        '''
        retval = ''
        for e in excludes:
            retval += '--exclude={} '.format(e)
        return retval

    def rsyncProbeDifferences(self, sourceTargetMap, excludes):
        '''
        For the given map of sources to targets return the number of files that
        exist on both sides but are different.
        '''
        retval = dict()
        for src, tgt in sourceTargetMap.iteritems():
            (rc, output) = syscmd(
                'rsync -rin --existing {} {}/ {}:{}'.format(self._exclRsyncStr(excludes), src, self._login, tgt))
            if rc != 0:
                print(output)
                print('Warning: cannot evaluate differences between {} and {}:{}', format(
                    src, self._login, tgt))
                continue
            diff_files = output.split('\n')
            retval[src] = len(diff_files) - 1 # minus 1 for the first line break we always have.
        return retval

    def countTargetFiles(self, sourceTargetMap, excludes):
        '''
        Counts files existing in target dirs
        '''
        retval = dict()
        for src, tgt in sourceTargetMap.iteritems():
            (rc, output) = syscmd('ssh {} ls -R1 {}'.format(self._login, tgt))
            if rc != 0:
                print(output)
                print('Warning: cannot count files in {}:{}', format(
                    self._login, tgt))
                continue

            # count lines excluding folder names and empty ones
            cnt = 0
            lines = output.split('\n')[1:]
            for l in lines:
                if l == '\n' or ':' in l:
                    continue
                excluded = False
                for e in excludes:
                    if str(e) in l:
                        excluded = True
                        break
                if excluded:
                    continue
                cnt += 1

            retval[src] = cnt # minus 1 for the first line break we always have.
        return retval

    def rsyncUpdateRemote(self, sourceTargetMap, excludes):
        '''
        For the given map of sources to targets update the remote files using rsync.
        '''
        for src, tgt in sourceTargetMap.iteritems():
            (rc, output) = syscmd(
                'rsync -arP --exclude={} {} {}:{}'.format(excludes, src, self._login, tgt))
            print(output)
            if rc != 0:
                print('Warning: cannot rsync from {} to {}:{}',
                      format(src, self._login, tgt))


class BackupConfigFile:
    def __init__(self, configfile):
        cf = open(args.configfile, 'r')
        cf_json = json.load(cf)
        cf.close()
        self._nodes = cf_json['nodes']
        self._excludes = cf_json['excludes']

    def nodes(self):
        return self._nodes

    def excludes(self):
        return self._excludes


########
ap = argparse.ArgumentParser()
ap.add_argument('-c', '--connection', required=True,
                help='ssh-like connection info, user@address.')
ap.add_argument('-f', '--configfile', required=True,
                help='JSON-file with configuration')
args = ap.parse_args()

osc = OffSiteConnect(args.connection)
cf = BackupConfigFile(args.configfile)

total = osc.countTargetFiles(cf.nodes(), cf.excludes())
print(total)
diffs = osc.rsyncProbeDifferences(cf.nodes(), cf.excludes())
print(diffs)
