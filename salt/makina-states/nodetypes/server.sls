{# Makina-states autodiscovery integration file, see the -standalone file #}
{% import "makina-states/nodetypes/server-standalone.sls" as base with context %}
{{base.do(full=True)}}
