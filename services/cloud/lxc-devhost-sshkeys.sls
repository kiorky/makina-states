{# specific install rules on devhost for lxc managment #}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.cloud.lxc-hooks
  - makina-states.nodetypes.vagrantvm-ssh-keys

{# copy user ssh keys for pull/push inside containers #}
cloud-lxc-devhost-sync-sshs:
  cmd.run:
    - name: |
            ls -d /var/lib/lxc/*/rootfs/root/ /var/lib/lxc/*/rootfs/home/*/ /var/lib/lxc/*/rootfs/home/users/*/ 2>/dev/null|while read homedir;do
                user=$(basename ${homedir});
                if [ "x$user}" != "xusers" ] && [ -e "${homedir}/.ssh" ];then
                  rsync -av "/root/.ssh/" "${homedir}/.ssh/";
                  chmod -Rf 700 "${homedir}/.ssh/";
                  chown -Rf "${user}:${user}" "${homedir}/.ssh/";
                fi
            done
    - user: root
    - require:
      - mc_proxy: salt-cloud-lxc-devhost-hooks
      - cmd: vagrantvm-install-ssh-keys
