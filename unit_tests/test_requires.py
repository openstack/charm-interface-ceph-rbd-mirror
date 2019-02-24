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

import mock
import requires

import charms_openstack.test_utils as test_utils


_hook_args = {}


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = []
        hook_set = {
            'when': {
                'joined': (
                    'endpoint.{endpoint_name}.joined',),
                'changed': (
                    'endpoint.{endpoint_name}.changed',),
            },
            'when_not': {
                'broken': ('endpoint.{endpoint_name}.joined',),
            },
        }
        # test that the hooks were registered
        self.registered_hooks_test_helper(requires, hook_set, defaults)


class TestCephRBDMirrorRequires(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.requires_class = requires.CephRBDMirrorRequires(
            'some-endpoint', [], unique_id='some-hostname')
        self._patches = {}
        self._patches_start = {}

    def tearDown(self):
        self.ceph_rbd_req = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch_requires_class(self, attr, return_value=None):
        mocked = mock.patch.object(self.requires_class, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def patch_topublish(self):
        self.patch_requires_class('_relations')
        relation = mock.MagicMock()
        to_publish = mock.PropertyMock()
        type(relation).to_publish = to_publish
        self._relations.__iter__.return_value = [relation]
        return relation.to_publish

    def test_joined(self):
        self.patch_object(requires, 'set_flag')
        self.requires_class.joined()
        self.set_flag.assert_called_once_with('some-endpoint.connected')

    def test_changed(self):
        self.patch_object(requires, 'all_flags_set')
        self.patch_object(requires, 'clear_flag')
        self.patch_object(requires, 'set_flag')
        self.all_flags_set.return_value = True
        self.requires_class.changed()
        self.all_flags_set.assert_called_with(
            'endpoint.some-endpoint.changed.auth',
            'endpoint.some-endpoint.changed.some-hostname_key',
            'endpoint.some-endpoint.changed.ceph-public-address',
        )
        self.clear_flag.assert_has_calls([
            mock.call('endpoint.some-endpoint.changed.auth'),
            mock.call('endpoint.some-endpoint.changed.some-hostname_key'),
            mock.call('endpoint.some-endpoint.changed.ceph-public-address'),
        ])
        self.set_flag.assert_called_once_with('some-endpoint.available')

    def test_broken(self):
        self.patch_object(requires, 'clear_flag')
        self.requires_class.broken()
        self.clear_flag.assert_has_calls([
            mock.call('some-endpoint.available'),
            mock.call('some-endpoint.connected'),
        ])

    def test_request_key(self):
        to_publish = self.patch_topublish()
        self.requires_class.request_key()
        to_publish.__setitem__.assert_called_with('unique_id', 'some-hostname')

    def test_mon_hosts(self):
        self.patch_requires_class('_relations')
        relation = mock.MagicMock()
        unit_incomplete = mock.MagicMock()
        unit_incomplete.received = {}
        unit_invalid = mock.MagicMock()
        unit_invalid.received = {'ceph-public-address': None}
        unitv6 = mock.MagicMock()
        unitv6.received = {'ceph-public-address': '2001:db8:42::1'}
        unitv4 = mock.MagicMock()
        unitv4.received = {'ceph-public-address': '192.0.2.1'}
        relation.units.__iter__.return_value = [unit_incomplete, unitv6,
                                                unit_invalid, unitv4]
        self._relations.__iter__.return_value = [relation]
        self.assertEqual(list(self.requires_class.mon_hosts),
                         ['[2001:db8:42::1]:6789', '192.0.2.1:6789'])
