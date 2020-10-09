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

import json
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

    def test_create_replicated_pool(self):
        self.patch_requires_class('_relations')
        relation = mock.MagicMock()
        relation.relation_id = 'some-endpoint:42'
        self._relations.__iter__.return_value = [relation]
        self.patch_object(requires.ch_ceph, 'get_previous_request')
        broker_req = mock.MagicMock()
        broker_req.ops = [{'op': 'create-pool', 'name': 'rbd'}]
        self.get_previous_request.return_value = broker_req
        self.requires_class.create_replicated_pool('rbd')
        self.assertFalse(broker_req.add_op_create_replicated_pool.called)
        self.get_previous_request.return_value = None
        self.patch_object(requires.ch_ceph, 'CephBrokerRq')
        self.CephBrokerRq.return_value = broker_req
        self.requires_class.create_replicated_pool('rbd')
        self.CephBrokerRq.assert_called_with()
        self.assertFalse(broker_req.add_op_create_replicated_pool.called)
        broker_req = mock.MagicMock()
        self.CephBrokerRq.return_value = broker_req
        self.patch_object(requires.ch_ceph, 'send_request_if_needed')
        self.requires_class.create_replicated_pool('rbd')
        broker_req.add_op_create_replicated_pool.assert_called_once_with(
            app_name=None, group=None, max_bytes=None, max_objects=None,
            name='rbd', namespace=None, pg_num=None, replica_count=3,
            weight=None)
        self.send_request_if_needed.assert_called_once_with(
            broker_req,
            relation='some-endpoint')

    def test_create_erasure_pool(self):
        self.patch_requires_class('_relations')
        relation = mock.MagicMock()
        relation.relation_id = 'some-endpoint:42'
        self._relations.__iter__.return_value = [relation]
        self.patch_object(requires.ch_ceph, 'get_previous_request')
        broker_req = mock.MagicMock()
        broker_req.ops = [{'op': 'create-pool', 'name': 'rbd'}]
        self.get_previous_request.return_value = broker_req
        self.requires_class.create_erasure_pool('rbd')
        self.assertFalse(broker_req.add_op_create_erasure_pool.called)
        self.get_previous_request.return_value = None
        self.patch_object(requires.ch_ceph, 'CephBrokerRq')
        self.CephBrokerRq.return_value = broker_req
        self.requires_class.create_erasure_pool('rbd')
        self.CephBrokerRq.assert_called_with()
        self.assertFalse(broker_req.add_op_create_erasure_pool.called)
        broker_req = mock.MagicMock()
        self.CephBrokerRq.return_value = broker_req
        self.patch_object(requires.ch_ceph, 'send_request_if_needed')
        self.requires_class.create_erasure_pool('rbd')
        broker_req.add_op_create_erasure_pool.assert_called_once_with(
            app_name=None, erasure_profile=None, group=None, max_bytes=None,
            max_objects=None, name='rbd', weight=None)
        self.send_request_if_needed.assert_called_once_with(
            broker_req,
            relation='some-endpoint')

    def test_refresh_pools(self):
        self.patch_object(requires.uuid, 'uuid4')
        self.uuid4.return_value = 'FAKE-UUID'
        to_publish = self.patch_topublish()
        self.requires_class.refresh_pools()
        to_publish.__setitem__.assert_called_with('nonce', 'FAKE-UUID')

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
        self.assertEqual(list(self.requires_class.mon_hosts()),
                         ['[2001:db8:42::1]:6789', '192.0.2.1:6789'])

    def test_public_network(self):
        self.patch_requires_class('_all_joined_units')
        self._all_joined_units.received.__getitem__.return_value = '192.0.2.1'
        self.patch_object(requires.ch_ip, 'resolve_network_cidr')
        self.resolve_network_cidr.return_value = '192.0.2.0/24'
        self.assertEqual(self.requires_class.public_network, '192.0.2.0/24')
        self._all_joined_units.received.__getitem__.assert_called_once_with(
            'ceph-public-address')
        self.resolve_network_cidr.assert_called_once_with('192.0.2.1')

    def test_cluster_network(self):
        self.patch_requires_class('_all_joined_units')
        self._all_joined_units.received.__getitem__.return_value = '192.0.2.1'
        self.patch_object(requires.ch_ip, 'resolve_network_cidr')
        self.resolve_network_cidr.return_value = '192.0.2.0/24'
        self.assertEqual(self.requires_class.cluster_network, '192.0.2.0/24')
        self._all_joined_units.received.__getitem__.assert_called_once_with(
            'ceph-cluster-address')
        self.resolve_network_cidr.assert_called_once_with('192.0.2.1')

    def test_maybe_send_rq(self):
        self.patch_requires_class('_relations')
        relation = mock.MagicMock()
        self._relations.__iter__.return_value = [relation]
        self.patch_object(requires.ch_ceph, 'send_request_if_needed')
        self.requires_class.maybe_send_rq('aRq')
        self.send_request_if_needed.assert_called_once_with(
            'aRq', relation='some-endpoint')

    def test_broker_requests(self):
        self.patch_requires_class('_all_joined_units')
        self._all_joined_units.received.__contains__.return_value = True
        self._all_joined_units.received.__getitem__.return_value = [
            json.dumps({'fakereq': 0}),
            json.dumps({'fakereq': 1}),
        ]
        for rq in self.requires_class.broker_requests:
            self.assertIn(rq['fakereq'], (0, 1))
        self._all_joined_units.received.__contains__.return_value = False
        with self.assertRaises(StopIteration):
            next(self.requires_class.broker_requests)
        self._all_joined_units.received.__contains__.return_value = True
        self._all_joined_units.received.__getitem__.return_value = None
        with self.assertRaises(StopIteration):
            next(self.requires_class.broker_requests)
