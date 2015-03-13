#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_cloud_vm:

mc_cloud_vm / vm registry for compute nodes
===============================================



'''
__docformat__ = 'restructuredtext en'

# Import python libs
import logging
import mc_states.utils
import os
import copy


from mc_states import saltapi
from salt.utils.odict import OrderedDict
from mc_states.utils import memoize_cache

__name = 'mc_cloud_vm'

log = logging.getLogger(__name__)
VT = 'vm'
PREFIX = 'makina-states.cloud.vms'


def vt(vt=VT):
    return vt


def vt_default_settings(cloudSettings, imgSettings, ttl=60):
    '''
    VM default settings
    This may be needed to be database backended in the future.
    As well, we may need iterator loops inside jinja templates
    to not eat that much memory loading large datasets.

    makina-states.services.cloud.lxc
        The settings of lxc containers that are meaningful on the
        cloud controller

    cloud defaults (makina-states.services.cloud.lxc)
        defaults settings to provision lxc containers
        Those are all redefinable at each container level

        LXC API:

        mode
            (salt (default) or mastersalt)

        ssh_gateway
            ssh gateway info
        ssh_gateway_port
            ssh gateway info
        ssh_gateway_user
            ssh gateway info
        ssh_gateway_key
            ssh gateway info
        size
            default filesystem size for container on lvm
            None
        gateway
            10.5.0.1
        master
            master to uplink the container to
            None
        master_port
            '4506'
        image
            LXC template to use
            'ubuntu'
        network
            '10.5.0.0'
        netmask
            '16'
        netmask_full
            '255.255.0.0'
        autostart
            lxc is autostarted
        bridge
            we install via states a bridge in 10.5/16 lxcbr1)
            'lxcbr1'
        sudo
            True
        use_bridge
            True
        users
            ['root', 'sysadmin']
        ssh_username
            'ubuntu'
        vgname
            'data'
        lvname
            'data'

    vms
        List of containers ids classified by host ids::

            (Mapping of {hostid: [vmid]})

        The settings are not stored here for obvious performance reasons
    '''
    def _do(cloudSettings, imgSettings):
        _s = __salt__
        _g = __grains__
        default_snapshot = False
        if _s['mc_nodetypes.is_devhost']():
            default_snapshot = True
        vt_settings = {
            'vt': VT,
            'defaults': {
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                #
                'image': 'ubuntu',
                'snapshot': default_snapshot,
                'autostart': True,
                #
                'target': None,
                'gateway': '127.0.0.1',
                'use_bridge': True,
                'main_bridge': 'br0',
                'ip': None,
                'mac': None,
                'netmask': '16',
                'network': '10.3.0.0',
                'netmask_full': '255.255.0.0',
                'bridge': 'br0',
                'additional_ips': [],
                'name': _g['id'],
                'domains': [_g['id']],
                'ssl_certs': [],
                #
                'ssh_gateway': cloudSettings['ssh_gateway'],
                'ssh_username': 'ubuntu',
                'ssh_gateway_password': cloudSettings[
                    'ssh_gateway_password'],
                'ssh_gateway_user': cloudSettings['ssh_gateway_user'],
                'ssh_gateway_key': cloudSettings['ssh_gateway_key'],
                'ssh_gateway_port': cloudSettings['ssh_gateway_port'],
                #
                'master': cloudSettings['master'],
                'mode': cloudSettings['mode'],
                'master_port': cloudSettings['master_port'],
                'bootsalt_branch': cloudSettings['bootsalt_branch'],
                'bootstrap_shell': cloudSettings['bootstrap_shell'],
                'script': cloudSettings['script'],
                'script_args': cloudSettings['bootsalt_mastersalt_args'],
                #
                'ssh_reverse_proxy_port': None,
                'snmp_reverse_proxy_port': None,
                #
                'password': None,
                'sudo': True,
                'users': ['root', 'sysadmin'],
                #
                'size': None,  # via profile
                'backing': 'lvm',
                'pools': [{'name': 'vg', 'type': 'lvm'}]
            },
            'vms': OrderedDict(),
        }
        return vt_settings
    cache_key = 'mc_cloud_vm.default_settings'
    return copy.deepcopy(
        memoize_cache(_do, [cloudSettings, imgSettings], {}, cache_key, ttl))


def vm_default_settings(vm, cloudSettings, imgSettings, extpillar=False):
    '''
    Get per VM specific settings
     All the defaults defaults registry settings are redinable here +
    This is for the moment the only backend of corpus cloud infra.
    If you want to implement another backend, mimic the dictionnary
    for this method and also settings.

        Corpus API

        ip
            do not set it, or use at ure own risk, prefer just to read the
            value. This is the main ip (private network)
        additional_ips
            additionnal ips which will be wired on the main bridge (br0)
            which is connected to internet.
            Be aware that you may use manual virtual mac addresses
            providen by you provider (online, ovh, sys).
            This is a list of mappings {ip: '', mac: '',netmask:''}
            eg::

                makina-states.cloud.lxc.vms.<target>.<name>.additionnal_ips:
                  - {'mac': '00:16:3e:01:29:40',
                     'gateway': None, (default)
                     'link': 'br0', (default)
                     'netmask': '32', (default)
                     'ip': '22.1.4.25'}
        domains
            list of domains tied with this host (first is minion id
            and main domain name, it is automaticly added)
    '''
    _s = __salt__
    vm_infos = _s['mc_cloud_compute_node.get_vm'](vm)
    target, vt = vm_infos['target'], vm_infos['vt']
    if extpillar:
        vt_settings = _s['mc_cloud_vm.vt_extpillar'](target, vt)
    else:
        vt_settings = _s['mc_cloud_vm.vt_default_settings'.format(vt)](
            cloudSettings, imgSettings)

    # if it is not a distant minion, use private gateway ip
    master = vt_settings['defaults']['master']
    if _s['mc_pillar.mastersalt_minion_id']() == target:
        master = vt_settings['defaults']['gateway']
    node = 'mc_cloud_compute_node.'
    data = _s['mc_utils.dictupdate'](vt_settings['defaults'], {
        'name': vm,
        'vt': vt_settings['vt'],
        'target': target,
        'master': master,
        'domains': [vm],
        'ssh_reverse_proxy_port':  _s[node + 'get_ssh_port'](vm),
        'snmp_reverse_proxy_port': _s[node + 'get_snmp_port'](vm)})
    return copy.deepcopy(data)


def vm_registry(prefixed=True):
    prefix = PREFIX + "."
    if not prefixed:
        prefix = ''
    data = OrderedDict([('{0}vts'.format(prefix), OrderedDict()),
                        ('{0}vms'.format(prefix), OrderedDict())])
    return data


def vt_extpillar_settings(vt, ttl=60):
    def _do(vt):
        _s = __salt__
        fun = 'mc_cloud_{0}.vt_default_settings'.format(vt)
        extdata = _s['mc_pillar.get_global_clouf_conf'](vt)
        cloudSettings = _s['mc_cloud.extpillar_settings']()
        imgSettings = _s['mc_cloud_images.extpillar_settings']()
        data = cloudSettings = _s['mc_utils.dictupdate'](
            _s[fun](cloudSettings, imgSettings), extdata)
        return data
    cache_key = 'mc_cloud_vm.vt_extpillar_settings{0}'.format(vt)
    return memoize_cache(_do, [vt], {}, cache_key, ttl)


def vm_extpillar_settings(vm, ttl=30):
    _s = __salt__

    def _sort_domains(dom):
        if dom == vm:
            return '0{0}'.format(dom)
        else:
            return '1{0}'.format(dom)

    def _do(vm):
        cloudSettings = _s['mc_cloud.extpillar_settings']()
        imgSettings = _s['mc_cloud_images.extpillar_settings']()
        data = _s['mc_pillar.get_cloud_conf_for_vm'](vm)
        data = _s['mc_utils.dictupdate'](
            vm_default_settings(
                vm, cloudSettings, imgSettings, extpillar=True),
            data)
        find_ip = 'mc_cloud_compute_node.find_ip_for_vm'
        data['ip'] = _s[find_ip](vm,
                                 network=data['network'],
                                 netmask=data['netmask'],
                                 default=data.get('ip'))
        data['mac'] = _s['mc_cloud_compute_node.find_mac_for_vm'](
            vm, default=data.get('mac', None))
        data['password'] = _s[
            'mc_cloud_compute_node.find_password_for_vm'
        ](vm, default=_s['mc_pillar.get_passwords'](vm)['clear']['root'])
        data = saltapi.complete_gateway(data, data)
        if vm not in data['domains']:
            data['domains'].insert(0, vm)
        data['domains'].sort(key=_sort_domains)
        if (
            ('-b' not in data['script_args'])
            and ('--branch' not in data['script_args'])
        ):
            data['script_args'] += ' -b {0}'.format(
                data['bootsalt_branch'])
        # at this stage, only get already allocated ips

        for ix, ipinfos in enumerate(data['additional_ips']):
            k = '{0}_{1}_{2}_aip_fo'.format(data['target'], vm, ix)
            mac = ipinfos.setdefault('mac', None)
            if not mac:
                mac = _s['mc_cloud_compute_node.get_conf_for_vm'](
                    vm, k, default=mac)
            if not mac:
                _s['mc_cloud_compute_node.set_conf_for_vm'](
                    vm, k, _s['mc_cloud_compute_node.gen_mac']())
            ipinfos['mac'] = mac
            ipinfos.setdefault('gateway', None)
            if ipinfos['gateway']:
                data['gateway'] = None
            ipinfos.setdefault('netmask', '32')
            ipinfos.setdefault('link', 'br0')
        return data
    cache_key = 'mc_cloud_vm.extpillar_settings{0}'.format(vm)
    return memoize_cache(_do, [vm], {}, cache_key, ttl)


def vt_extpillar(target, vt, ttl=60):
    def _do(target, vt):
        _s = __salt__
        extdata = _s['mc_pillar.get_cloud_conf_for_cn'](target).get(vt, {})
        data = vt_extpillar_settings(vt)
        fun = 'mc_cloud_{0}.vt_extpillar'.format(vt)
        data = _s['mc_utils.dictupdate'](_s[fun](target, data), extdata)
        return data
    cache_key = 'mc_cloud_vm.vt_extpillar{0}{1}'.format(target, vt)
    return memoize_cache(_do, [target, vt], {}, cache_key, ttl)


def domains_for(vm, domains=None):
    _s = __salt__
    if domains is None:
        vm_settings = _s['mc_cloud_vm.vm_extpillar_settings'](vm)
        domains =vm_settings['domains']
    # special case as domains is a list but we always want for
    # the vm id to be un domains list even if overriden in
    # extpillar
    domains = _s['mc_utils.uniquify']([vm] + domains)
    return domains


def vm_extpillar(id_, ttl=60):
    def _do(id_):
        _s = __salt__
        extdata = _s['mc_pillar.get_cloud_conf_for_vm'](id_)
        data = vm_extpillar_settings(id_)
        fun = 'mc_cloud_{0}.vm_extpillar'.format(data['vt'])
        data = _s['mc_utils.dictupdate'](_s[fun](id_, data), extdata)
        data['domains'] = domains_for(id_, data['domains'])
        data['ssl_certs'] = _s['mc_cloud.ssl_certs_for'](
            id_, data['domains'], data['ssl_certs'])
        _s['mc_cloud.add_ms_ssl_certs'](data)
        return data
    cache_key = 'mc_cloud_vm.vm_extpillar{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def ext_pillar(id_, prefixed=True, ttl=60, *args, **kw):
    def _do(id_, prefixed):
        _s = __salt__
        all_vms = _s['mc_cloud_compute_node.get_vms']()
        targets = _s['mc_cloud_compute_node.get_targets']()
        vms, vts = OrderedDict(), []
        target = None
        if id_ not in targets and id_ not in all_vms:
            return {}
        if id_ in all_vms:
            vt = all_vms[id_]['vt']
            if vt not in vts:
                vts.append(vt)
            vms[id_] = all_vms[id_]
            target = all_vms[id_]['target']
        if id_ in targets:
            target = id_
            for vm_, vmdata_ in targets[id_]['vms'].items():
                vms[vm_] = vmdata_
            [vts.append(i) for i in targets[id_]['vts']
             if i not in vts]
        data = vm_registry(prefixed=prefixed)
        if prefixed:
            vts_pillar = data[PREFIX + '.vts']
            vms_pillar = data[PREFIX + '.vms']
        else:
            vts_pillar = data['vts']
            vms_pillar = data['vms']
        for vt in vts:
            vts_pillar[vt] = _s['mc_cloud_vm.vt_extpillar'](target, vt)
        for vm, vmdata in vms.items():
            vt = vmdata['vt']
            vm_settings = _s['mc_cloud_vm.vm_extpillar'](vm)
            vm_settings['vt'] = vt
            vms_pillar[vm] = vm_settings
            _s['mc_cloud.add_ms_ssl_certs'](data, vm_settings)
        return data
    cache_key = 'mc_cloud_vm.ext_pillar{0}{1}'.format(id_, prefixed)
    return memoize_cache(_do, [id_, prefixed], {}, cache_key, ttl)


'''
Methods usable
After the pillar has loaded, on the compute node itself
'''


def settings(ttl=60):
    def _do():
        _s = __salt__
        settings = _s['mc_utils.defaults'](PREFIX, vm_registry(prefixed=False))
        return settings
    cache_key = '{0}.{1}'.format(__name, 'settings')
    return memoize_cache(_do, [], {}, cache_key, ttl)


def vt_settings(vt=VT, ttl=60):
    def _do(vt):
        _s = __salt__
        data = settings()['vms'].get(vt, {})
        if data:
            vt_fun = 'mc_cloud_{0}.vt_default_settings'.format(vt)
            cloudSettings = _s['mc_cloud.settings']()
            imgSettings = _s['mc_cloud_images.settings']()
            data = _s['mc_utils.dictupdate'](
                data,  _s[vt_fun](cloudSettings, imgSettings))
        return data
    cache_key = '{0}.{1}{2}'.format(__name, 'vt_settings', vt)
    return memoize_cache(_do, [vt], {}, cache_key, ttl)


def vm_settings(id_=None, ttl=60):
    def _do(id_):
        if not id_:
            id_ = __grains__['id']
        _s = __salt__
        data = settings()['vms'].get(id_, {})
        if data and ('vt' in 'data'):
            vt = data['vt']
            fun = 'mc_cloud_{0}.vm_default_settings'.format(vt)
            cloudSettings = _s['mc_cloud.settings']()
            imgSettings = _s['mc_cloud_images.settings']()
            data = _s['mc_utils.dictupdate'](
                data, _s[fun](cloudSettings, imgSettings))
        return data
    cache_key = '{0}.{1}{2}'.format(__name, 'vts_settings', id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def vts_settings(ttl=60):
    def _do():
        data = OrderedDict()
        for vt in data['vts']:
            data[vt] = vt_settings(vt)
        return data
    cache_key = '{0}.{1}'.format(__name, 'vts_settings')
    return memoize_cache(_do, [], {}, cache_key, ttl)


def vms_settings(ttl=60):
    def _do():
        data = OrderedDict()
        for id_ in data['vms']:
            data[id_] = vm_settings(id_)
        return data
    cache_key = '{0}.{1}'.format(__name, 'vms_settings')
    return memoize_cache(_do, [], {}, cache_key, ttl)
# vim:set et sts=4 ts=4 tw=81: