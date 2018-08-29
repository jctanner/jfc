# (c) 2018, Ansible Project
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import subprocess
from ansible.plugins.action import ActionBase


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def run_command(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (so, se) = p.communicate()
    return (p.returncode, so, se)


class PRModuleLoader(object):

    def __init__(self, srcurl, cachedir=None):
        self.cachedir = cachedir
        self.srcurl = srcurl
        self.owner, self.repo, self.number = self.split_pull_url(self.srcurl)
        self.checkout_dir = os.path.join(
            self.cachedir,
            self.owner + '.' + self.repo + '.' + str(self.number)
        )
        self.clone_pr()


    def split_pull_url(self, src):
        # http://github.com/ansible/ansible/pull/44698
        parts = src.split('/')
        return (parts[3], parts[4], parts[-1])
        

    def clone_pr(self):
        '''
        git clone https://github.com/ansible/ansible --recursive ansible.ansible 
        cd $CWD/ansible.ansible
        git fetch origin pull/$TICKETID/head:TEST_$TICKETID
        git checkout TEST_$TICKETID
        '''

        if not os.path.exists(self.checkout_dir):
            cmd = 'git clone https://github.com/%s/%s %s' % (self.owner, self.repo, self.checkout_dir)
            (rc, so, se) = run_command(cmd)
            if rc != 0:
                raise Exception(se)
            cmd = 'cd %s; git fetch origin pull/%s/head:TEST_%s' % (self.checkout_dir, self.number, self.number)
            (rc, so, se) = run_command(cmd)
            if rc != 0:
                raise Exception(se)
            cmd = 'cd %s; git checkout TEST_%s' % (self.checkout_dir, self.number)
            (rc, so, se) = run_command(cmd)
            if rc != 0:
                raise Exception(se)


    def find_module_files(self, name):

        BLACKLIST = ['ansible.module_utils.basic', 'ansible.module_utils._text']

        cmd = 'find %s -type f -name "%s.py"' % (self.checkout_dir, name)
        (rc, so, se) = run_command(cmd)
        fns = [x.strip() for x in so.split('\n') if x.strip()]
        for fn in fns[:]:
            cmd = 'egrep ^"from ansible." %s' % fn
            (rc, so, se) = run_command(cmd)
            imports = [x.strip() for x in so.split('\n') if x.strip()]
            for _import in imports:
                base = _import.split()[1]
                if base not in BLACKLIST:
                    util_name = base.split('.')[-1]
                    util_file = os.path.join(self.checkout_dir, 'lib', 'ansible', 'module_utils', util_name + '.py')
                    fns.append(util_file)

        #import epdb; epdb.st()
        return fns




class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    # CONFIG
    CACHEDIR = os.path.expanduser('~/.jfc')
    PULLCACHE = os.path.join(CACHEDIR, 'pulls')

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = True
        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if not os.path.exists(self.CACHEDIR):
            os.makedirs(self.CACHEDIR)
        if not os.path.exists(self.PULLCACHE):
            os.makedirs(self.PULLCACHE)

        src = self._task.args.get('src')
        module = self._task.args.get('name')
        module_args = self._task.args.get('args')

        if src.startswith('http') and 'github.com' in src and 'pull' in src:
            PRML = PRModuleLoader(src, cachedir=self.PULLCACHE)
            mfiles = PRML.find_module_files(module)
            self._shared_loader_obj.module_loader._plugin_path_cache['.py'][module] = mfiles[0]
            self._shared_loader_obj.module_loader._plugin_path_cache[''][module] = mfiles[0]
            result = self._execute_module(module_name=module, module_args=module_args, task_vars=task_vars)
            return result
        else:
            raise Exception('NOT IMPLEMENTED')

        return {}
