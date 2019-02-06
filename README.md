# Overview

This interface handles the communication between the Ceph Monitor cluster
and a RBD Mirror client that has specific access key requirements.

# Usage

No explicit handler is required to consume this interface in charms
that consume this interface.

In addittion to the states automatically set based on relation data by
``charms.reactive.Endpoint``, the interface provides the
``{{endpoint_name}}.available`` state.

# metadata

To consume this interface in your charm or layer, add the following to `layer.yaml`:

```yaml
includes: ['interface:ceph-rbd-mirror']
```

and add a requires interface of type `ceph-rbd-mirror` to your charm or layers `metadata.yaml`:

```yaml
requires:
  ceph-local:
    interface: ceph-rbd-mirror
  ceph-remote:
    interface: ceph-rbd-mirror
```

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/openstack-charms/+filebug).

For development questions please refer to the OpenStack [Charm Guide](https://github.com/openstack/charm-guide).
