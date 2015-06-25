include:
  - makina-states.nodetypes.vm
  - makina-states.localsettings.pkgs.hooks
  - makina-states.nodetypes.container-hooks

lxc-container-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - apt-utils
      - libfuse2
    - watch:
      - mc_proxy: makina-lxc-proxy-pkgs-pre
    - watch_in:
      - mc_proxy: makina-lxc-proxy-pkgs

etc-init-lxc-setup:
  file.managed:
    - name: /etc/init/lxc-setup.conf
    - source: salt://makina-states/files/etc/init/lxc-setup.conf
    - user: root
    - group: root
    - mode: 0755
    - watch:
      - mc_proxy: makina-lxc-proxy-pkgs
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cfg

{% set extra_confs = {'/usr/bin/ms-lxc-setup.sh': {"mode": "755"},
                      '/etc/systemd/system/lxc-stop.service': {"mode": "644"},
                      '/etc/systemd/system/lxc-setup.service': {"mode": "644"},
                      '/usr/bin/ms-lxc-stop.sh': {"mode": "755"}} %}
{% for f, fdata in extra_confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
lxc-conf-{{f}}:
  file.managed:
    - name: "{{fdata.get('target', f)}}"
    - source: "{{fdata.get('source', 'salt://makina-states/files'+f)}}"
    - mode: "{{fdata.get('mode', 750)}}"
    - user: "{{fdata.get('user', 'root')}}"
    - group:  "{{fdata.get('group', 'root')}}"
    {% if fdata.get('makedirs', True) %}
    - makedirs: true
    {% endif %}
    {% if template %}
    - template: "{{template}}"
    {%endif%}
    - watch:
      - mc_proxy: makina-lxc-proxy-cfg
    - watch_in:
      - mc_proxy: makina-lxc-proxy-dep
{% endfor %}

lxc-cleanup:
  file.managed:
    - name: /sbin/lxc-cleanup.sh
    - source: salt://makina-states/files/sbin/lxc-cleanup.sh
    - user: root
    - group: root
    - mode: 0755
    - watch:
      - mc_proxy: makina-lxc-proxy-pkgs
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cfg

etc-init-lxc-stop:
  file.managed:
    - name: /etc/init/lxc-stop.conf
    - source: salt://makina-states/files/etc/init/lxc-stop.conf
    - user: root
    - group: root
    - mode: 0755
    - watch:
      - mc_proxy: makina-lxc-proxy-pkgs
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cfg

lxc-install-non-harmful-packages:
  file.managed:
    - source: salt://makina-states/_scripts/build_lxccorepackages.sh
    - name: /sbin/build_lxccorepackages.sh
    - user: root
    - group: root
    - mode: 750
    - watch:
      - mc_proxy: makina-lxc-proxy-pkgs
    - watch_in:
      - mc_proxy: makina-lxc-proxy-cfg
  cmd.run:
    - name: /sbin/build_lxccorepackages.sh
    - watch:
      - mc_proxy: makina-lxc-proxy-build
    - watch_in:
      - mc_proxy: makina-lxc-proxy-mark

do-lxc-cleanup:
  cmd.run:
    - name: /sbin/lxc-cleanup.sh
    - watch:
      - mc_proxy: makina-lxc-proxy-cleanup
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end

{% if salt['mc_nodetypes.is_systemd']() and
salt['mc_nodetypes.is_container']() %}
# apply a patch to be sure that future evols of the
# script are still compatible with our work
# (this patch wont apply in other case)
do-systemd-sysv-patch:
  file.managed:
    - name: /tmp/systemd-initd.patch
    - source: salt://makina-states/files/lib/lsb/init-functions.d/40-systemd.patch
    - onlyif: |
              set -e
              test -e /lib/lsb/init-functions.d/40-systemd
              if grep -q makinacorpus_container_init /lib/lsb/init-functions.d/40-systemd;then exit 1;fi
    - watch:
      - mc_proxy: makina-lxc-proxy-cleanup
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end
  cmd.run:
    - cwd: /
    - name: |
            set -e
            patch --dry-run -Np2 < /tmp/systemd-initd.patch
            patch -Np2 < /tmp/systemd-initd.patch
    - onlyif: |
              set -e
              test -e /lib/lsb/init-functions.d/40-systemd
              test -e /tmp/systemd-initd.patch
              if grep -q makinacorpus_container_init /lib/lsb/init-functions.d/40-systemd;then exit 1;fi
    - watch:
      - file: do-systemd-sysv-patch
      - mc_proxy: makina-lxc-proxy-cleanup
    - watch_in:
      - mc_proxy: makina-lxc-proxy-end

# only enable, no stuff around
do-lxc-setup-services:
  cmd.run:
    - name:  |
        set -e
        systemctl enable lxc-setup
        systemctl enable lxc-stop
    - require:
      - mc_proxy: makina-lxc-proxy-cleanup
    - require_in:
      - mc_proxy: makina-lxc-proxy-end
{% endif %}
