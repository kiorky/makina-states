include:
  - makina-states.services.firewall.shorewall.disable
  - makina-states.services.firewall.firewalld.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.localsettings.network
firewalld-conflicting-services:
  service.dead:
    - names: [iptables, ebtables,
              shorewall, shorewall6]
    - enabled: false
    - watch:
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
firewalld:
  service.running:
    - enabled: true
    - names:
      - firewalld
    - require:
      - service: firewalld-conflicting-services
      - mc_proxy: firewalld-prerestart
    - require:
      - mc_proxy: firewalld-postrestart

firewalld-reapply:
  cmd.run:
    - name: /usr/bin/ms_firewalld.py
    - watch:
      - service: firewalld
      - mc_proxy: firewalld-prerestart
    - watch_in:
      - mc_proxy: firewalld-postrestart
{%endif %}
