include:
  - makina-states.localsettings.network.hooks
# retrocompat, wire into shorewall hooks
  - makina-states.services.firewall.shorewall.hooks
firewalld-preinstall:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-postdisable
      - mc_proxy: network-last-hook
    - watch_in:
      - mc_proxy: firewalld-postinstall
      - mc_proxy: firewalld-preconf
      - mc_proxy: firewalld-postconf
      - mc_proxy: firewalld-prerestart
firewalld-postinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewalld-preconf
      - mc_proxy: firewalld-postconf
      - mc_proxy: firewalld-prerestart
firewalld-preconf:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: firewalld-postconf
      - mc_proxy: firewalld-prerestart
      - mc_proxy: shorewall-prerestart
firewalld-postconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewalld-prerestart
      - mc_proxy: firewalld-postrestart
firewalld-prerestart:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-prerestart 
    - watch_in:
      - mc_proxy: firewalld-postrestart
firewalld-postrestart:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-postrestart 