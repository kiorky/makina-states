{% set ulogdSettings = salt['mc_ulogd.settings']() %}
include:
  - makina-states.services.log.ulogd.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
ulogd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - ulogd
    - watch:
      - mc_proxy: ulogd-pre-install-hook
    - watch_in:
      - mc_proxy: ulogd-pre-hardrestart-hook
      - mc_proxy: ulogd-post-install-hook
{%endif%}
