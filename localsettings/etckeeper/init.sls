{% set locs=salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'etckeeper') }}
{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.localsettings.etckeeper.hooks
{% set defaults = salt['mc_etckeeper.settings']() %}

etckeeper-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - git
      - etckeeper
    - watch_in:
      - mc_proxy: etckeeper-inst-pre
    - watch_in:
      - mc_proxy: etckeeper-inst-post


{%- for config, cdata in defaults.configs.items() %}
{% set mode = cdata.get('mode', '0700') %}
etckeeper-{{config}}:
  file.managed:
    - name: {{config}}
    - source : {{cdata.get('template', 'salt://makina-states/files'+config)}}
    - makedirs: True
    - template: jinja
    - user: root
    - group: root
    - mode: 750
    - watch:
      - mc_proxy: etckeeper-conf-pre
    - watch_in:
      - mc_proxy: etckeeper-conf-post
{% endfor %}

etckeeper-initial:
  cmd.run:
    - name: |
            /usr/bin/etckeeper init
            /usr/bin/etckeeper commit "Initial commit"
    - unless: test -d {{locs.conf_dir}}/.git
    - watch:
      - mc_proxy: etckeeper-run-pre
    - watch_in:
      - mc_proxy: etckeeper-run-hook

etckeeper-perms:
  file.managed:
    - name: {{locs.conf_dir}}/etckeeper/etckeeperperms.sh
    - source: ''
    - user: root
    - group: root
    - mode: 750
    - watch:
      - cmd: etckeeper-initial
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook
    - contents: |
                #!/usr/bin/env bash
                exec {{locs.resetperms }} --dmode 0700 --fmode 0700 --user "root" --group "root" --paths {{locs.conf_dir}}/.git
{# deactivated as soon or later it will be autocommited from
   makina-states.commin.autocommit
etckeeper-run:
  cmd.run:
    - name: {{locs.conf_dir}}/cron.daily/etckeeper "commit from salt"
    - watch:
      - mc_proxy: etckeeper-run-hook
      - cmd: etckeeper-initial
      - file: etckeeper-perms
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook
#}
{% endif %}
