{#- Install in full mode, see the standalone file !  #}
{% import  "makina-states/controllers/salt_master-standalone.sls" as base with context %}
{{base.do(full=True)}}
