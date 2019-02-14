# Copyright 2018 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ipaddress
import socket

# the reactive framework unfortunately does not grok `import as` in conjunction
# with decorators on class instance methods, so we have to revert to `from ...`
# imports
from charms.reactive import (
    Endpoint,
    clear_flag,
    set_flag,
    when,
    when_all,
    when_not,
)


class CephRBDMirrorRequires(Endpoint):
    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        set_flag(self.expand_name('{endpoint_name}.connected'))

    @when_all('endpoint.{endpoint_name}.changed.auth',
              'endpoint.{endpoint_name}.changed.key',
              'endpoint.{endpoint_name}.changed.ceph-public-address')
    def changed(self):
        for key in ('auth', 'key', 'ceph-public-address'):
            clear_flag(
                self.expand_name(
                    'endpoint.{endpoint_name}.changed.' + key))
        set_flag(self.expand_name('{endpoint_name}.available'))

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        clear_flag(self.expand_name('{endpoint_name}.available'))
        clear_flag(self.expand_name('{endpoint_name}.connected'))

    def request_key(self, unique_id=None):
        if not unique_id:
            unique_id = socket.gethostname()
        for relation in self.relations:
            relation.to_publish['unique_id'] = unique_id

    @property
    def mon_hosts(self):
        for relation in self.relations:
            for unit in relation.units:
                addr = ipaddress.ip_address(
                    unit.received['ceph-public-address'])
                port = 6789
                if isinstance(addr, ipaddress.IPv6Address):
                    yield '[{}]:{}'.format(addr, port)
                else:
                    yield '{}:{}'.format(addr, port)

    @property
    def key(self):
        return self.all_units.received['key']
