#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Chris Long <alcamie@gmail.com> <chlong@redhat.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = ''' '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(required=False, default=None, type='str'),
            name=dict(required=True, default=None, type='str'),
            args=dict(required=True, default=None, type='str'),
        ),
        supports_check_mode=True
    )
    result = {}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
