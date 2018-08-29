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


class JFCRoleLoader(object):

    def __init__(self, srcurl, cachedir=None):
        self.cachedir = cachedir
        self.srcurl = srcurl
        self.owner, self.repo = self.split_role_url(self.srcurl)
        self.checkout_dir = os.path.join(
            self.cachedir,
            self.owner + '.' + self.repo
        )
        self.clone_role()


    def split_role_url(self, src):
        # https://github.com/f500/ansible-dumpall
        parts = src.split('/')
        return (parts[3], parts[4])
        

    def clone_role(self):

        if not os.path.exists(self.checkout_dir):
            cmd = 'git clone https://github.com/%s/%s %s' % (self.owner, self.repo, self.checkout_dir)
            (rc, so, se) = run_command(cmd)
            if rc != 0:
                raise Exception(se)

    def do_role(self, action_plugin, action, role_args):

        # we import here to prevent a circular dependency with imports
        from ansible.playbook.block import Block
        from ansible.playbook.handler import Handler
        from ansible.playbook.task import Task
        from ansible.playbook.task_include import TaskInclude
        from ansible.playbook.role_include import IncludeRole
        from ansible.playbook.handler_task_include import HandlerTaskInclude
        from ansible.template import Templar

        # task_ds: {u'import_role': u'name=jfc'}
        # block: BLOCK(uuid=3c970ebc-f5b7-5e5a-59fe-...)(id=...)(parent=None)
        # role: None
        # variable_manager: <ansible.vars.manager.VariableManager object at ...>
        # loader: <ansible.parsing.dataloader.DataLoader object at ...>

        task_ds = {'include_role': 'name=' + self.repo}
        #task_ds.update(role_args)
        #import epdb; epdb.st()

        ir = IncludeRole.load(
            task_ds,
            block=None,
            role=None,
            task_include=None,
            variable_manager={},
            loader=None,
        )
        import epdb; epdb.st()

        # we set a flag to indicate this include was static
        ir.statically_loaded = True

        # template the role name now, if needed
        all_vars = variable_manager.get_vars(play=play, task=ir)
        templar = Templar(loader=loader, variables=all_vars)
        if templar._contains_vars(ir._role_name):
            ir._role_name = templar.template(ir._role_name)

        # uses compiled list from object
        blocks, _ = ir.get_block_list(variable_manager=variable_manager, loader=loader)
        task_list.extend(blocks)



class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    # CONFIG
    CACHEDIR = os.path.expanduser('~/.jfc')
    ROLECACHE = os.path.join(CACHEDIR, 'roles')

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = True
        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if not os.path.exists(self.CACHEDIR):
            os.makedirs(self.CACHEDIR)
        if not os.path.exists(self.ROLECACHE):
            os.makedirs(self.ROLECACHE)

        src = self._task.args.get('src')
        action = self._task.args.get('action')
        role_args = self._task.args.get('args')

        if src.startswith('http') and 'github.com' in src:
            JRL = JFCRoleLoader(src, cachedir=self.ROLECACHE)
            JRL.do_role(self, action, role_args)

            '''
            self._shared_loader_obj.module_loader._plugin_path_cache['.py'][module] = mfiles[0]
            self._shared_loader_obj.module_loader._plugin_path_cache[''][module] = mfiles[0]
            result = self._execute_module(module_name=module, module_args=module_args, task_vars=task_vars)
            return result
            '''
        else:
            raise Exception('NOT IMPLEMENTED')

        return {}
