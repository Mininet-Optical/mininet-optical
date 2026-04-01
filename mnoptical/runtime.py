"""
runtime.py: runtime optical lightpath state and orchestration helpers
"""

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc).isoformat()


def _canonical_edge(a, b):
    return tuple(sorted((a, b)))


class RuntimeLightpathManager:
    """Track runtime optical state and delegate install/remove work."""

    def __init__(
        self, net, topology, ports, wavelengths,
        entry_factory, apply_entries,
        telemetry_factory=None
    ):
        self.net = net
        self.topology = deepcopy(topology)
        self.ports = deepcopy(ports)
        self.wavelengths = list(wavelengths)
        self.entry_factory = entry_factory
        self.apply_entries = apply_entries
        self.telemetry_factory = telemetry_factory or (lambda: [])
        self.active_lightpaths = {}
        self.edge_wavelength_usage = defaultdict(set)
        self.flow_sequence = 0

    def topology_graph(self):
        payload = deepcopy(self.topology)
        payload.setdefault('wavelengths', list(self.wavelengths))
        payload.setdefault('generated_at', _utcnow())
        return payload

    def topology_ports(self):
        return deepcopy(self.ports)

    def optical_state(self):
        usage = {
            '%s|%s' % edge: sorted(channels)
            for edge, channels in sorted(self.edge_wavelength_usage.items())
        }
        return {
            'active_lightpaths': [
                deepcopy(entry)
                for entry in sorted(
                    self.active_lightpaths.values(),
                    key=lambda item: item['flow_id']
                )
            ],
            'edge_wavelength_usage': usage,
            'active_lightpath_count': len(self.active_lightpaths),
            'wavelengths': list(self.wavelengths),
            'generated_at': _utcnow(),
        }

    def telemetry_links(self):
        data = self.telemetry_factory()
        return data if isinstance(data, list) else []

    def next_flow_id(self):
        self.flow_sequence += 1
        return 'flow-%d' % self.flow_sequence

    def _edge_ids(self, path):
        return [_canonical_edge(a, b) for a, b in zip(path, path[1:])]

    def _rebuild_usage(self):
        usage = defaultdict(set)
        for entry in self.active_lightpaths.values():
            for edge in entry.get('edge_ids', []):
                usage[_canonical_edge(*edge)].add(int(entry['wavelength']))
        self.edge_wavelength_usage = usage

    def _ensure_wavelength_available(self, flow_id, path, wavelength):
        wavelength = int(wavelength)
        for edge in self._edge_ids(path):
            users = [
                entry for entry in self.active_lightpaths.values()
                if entry['flow_id'] != flow_id
                and edge in {
                    _canonical_edge(*item) for item in entry.get('edge_ids', [])
                }
                and int(entry['wavelength']) == wavelength
            ]
            if users:
                return False, {
                    'edge': list(edge),
                    'wavelength': wavelength,
                    'conflicts_with': [entry['flow_id'] for entry in users],
                }
        return True, None

    def install_lightpath(self, request):
        payload = deepcopy(request or {})
        flow_id = payload.get('flow_id') or self.next_flow_id()
        path = list(payload.get('path') or [])
        wavelength = payload.get('wavelength')

        if len(path) < 2:
            return {
                'status': 'blocked',
                'flow_id': flow_id,
                'failure_reason': 'path must contain at least two nodes',
            }
        if wavelength is None:
            return {
                'status': 'blocked',
                'flow_id': flow_id,
                'failure_reason': 'wavelength is required',
            }

        ok, conflict = self._ensure_wavelength_available(flow_id, path, wavelength)
        if not ok:
            return {
                'status': 'blocked',
                'flow_id': flow_id,
                'failure_reason': 'wavelength unavailable on path',
                'conflict': conflict,
            }

        existing = self.active_lightpaths.get(flow_id)
        if existing is not None:
            self.active_lightpaths.pop(flow_id, None)

        entry = self.entry_factory(payload, deepcopy(self.active_lightpaths))
        if not isinstance(entry, dict):
            if existing is not None:
                self.active_lightpaths[flow_id] = existing
            return {
                'status': 'blocked',
                'flow_id': flow_id,
                'failure_reason': 'entry_factory did not return a lightpath entry',
            }

        entry['flow_id'] = flow_id
        entry['path'] = list(path)
        entry['wavelength'] = int(wavelength)
        entry['channel'] = int(wavelength)
        entry['edge_ids'] = [list(edge) for edge in self._edge_ids(path)]
        entry.setdefault('status', 'active')
        entry.setdefault('installed_at', _utcnow())
        entry['updated_at'] = _utcnow()

        self.active_lightpaths[flow_id] = entry

        try:
            self.apply_entries([
                deepcopy(item)
                for item in sorted(
                    self.active_lightpaths.values(),
                    key=lambda active: active['flow_id']
                )
            ])
        except Exception as exc:
            self.active_lightpaths.pop(flow_id, None)
            if existing is not None:
                self.active_lightpaths[flow_id] = existing
            self._rebuild_usage()
            return {
                'status': 'blocked',
                'flow_id': flow_id,
                'failure_reason': str(exc),
            }

        self._rebuild_usage()
        return {
            'status': 'installed',
            'flow_id': flow_id,
            'lightpath': deepcopy(entry),
        }

    def remove_lightpath(self, request):
        payload = deepcopy(request or {})
        flow_id = payload.get('flow_id')
        if not flow_id:
            return {'status': 'missing-flow-id', 'removed': False}

        removed = self.active_lightpaths.pop(flow_id, None)
        if removed is None:
            return {'status': 'not-found', 'removed': False, 'flow_id': flow_id}

        try:
            self.apply_entries([
                deepcopy(item)
                for item in sorted(
                    self.active_lightpaths.values(),
                    key=lambda active: active['flow_id']
                )
            ])
        except Exception as exc:
            self.active_lightpaths[flow_id] = removed
            self._rebuild_usage()
            return {
                'status': 'error',
                'removed': False,
                'flow_id': flow_id,
                'failure_reason': str(exc),
            }

        self._rebuild_usage()
        return {'status': 'removed', 'removed': True, 'flow_id': flow_id}
