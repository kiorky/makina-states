# -*- coding: utf-8 -*
'''
Salt related variables
============================================

'''

import unittest
# Import salt libs
import salt.utils
import os
import salt.utils.dictupdate
import salt.utils

__name = 'services'


def _metadata(REG):
    return __salt__['mc_macros.metadata'](
        __name, bases=['localsettings'])


def get_reg():
    return __salt__['mc_macros.registry_kind_get'](__name)


def set_reg(reg):
    return __salt__['mc_macros.registry_kind_set'](__name, reg)


def metadata():
    REG = get_reg()
    ret = REG.setdefault('metadata', _metadata(REG))
    set_reg(REG)
    return ret


def _settings(REG):
    resolver = __salt__['mc_utils.format_resolve']
    metadata = __salt__['mc_{0}.metadata'.format(__name)]()
    nodetypes_registry = __salt__['mc_nodetypes.registry']()
    localsettings = __salt__['mc_localsettings.settings']()
    pillar = __pillar__
    grains = __grains__
    locs = localsettings['locations']
    #
    # SSL Settings
    #
    SSLSettings = localsettings['SSLSettings']

    # ----------------------------------------------------
    # LDAP integration
    #
    ldapVariables = localsettings['ldapVariables']
    ldapEn = localsettings['ldapEn']

    #
    # SSHD Settings
    #
    sshServerSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.ssh.server', {
            'AuthorizedKeysFile': (
                '.ssh/authorized_keys .ssh/authorized_keys2'),
            'ChallengeResponseAuthentication': 'no',
            'X11Forwarding': 'yes',
            'PrintMotd': 'no',
            'UsePrivilegeSeparation': 'sandbox',
            'Banner': '/etc/ssh/banner',
            'UsePAM': 'yes',
        })

    #
    # SSH
    #
    sshClientSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.ssh.client', {
            'StrictHostKeyChecking': 'no',
            'UserKnownHostsFile': '/dev/null',
            'AddressFamily': 'any',
            'ConnectTimeout': 0,
            'SendEnv': "LANG: LC_*",
            'HashKnownHosts': 'yes',
            'GSSAPIAuthentication': 'yes',
            'GSSAPIDelegateCredentials': 'no',
        })

    # ----------------------------------------------------
    # init systems flags
    #
    upstart = __salt__['mc_utils.get']('makina-states.upstart', False)

    # ----------------------------------------------------
    # ntp is not applied to LXC containers ! (services.base.ntp)
    # So we will just match when our grain is set and not have a value of lxc
    #
    ntpEn = (
        not (
            ('dockercontainer' in nodetypes_registry['actives'])
            or ('lxccontainer' in nodetypes_registry['actives'])
        ))

    #
    # Apache:  (services.http.apache)
    #
    apacheStepOne = __salt__['grains.filter_by']({
        'dev': {
            'mpm': 'worker',
            'version': '2.2',
            'Timeout': 120,
            'KeepAlive': True,
            'MaxKeepAliveRequests': 5,
            'KeepAliveTimeout': 5,
            'log_level': 'warn',
            'serveradmin_mail': 'webmaster@localhost',
            'prefork': {
                'StartServers': 5,
                'MinSpareServers': 5,
                'MaxSpareServers': 5,
                'MaxClients': 20,
                'MaxRequestsPerChild': 300
            },
            'worker': {
                'StartServers': 2,
                'MinSpareThreads': 25,
                'MaxSpareThreads': 75,
                'ThreadLimit': 64,
                'ThreadsPerChild': 25,
                'MaxRequestsPerChild': 300,
                'MaxClients': 200
            },
            'event': {
                'AsyncRequestWorkerFactor': "1.5"
            },
            'register-sites': {}
        },
        'prod': {
            'mpm': 'worker',
            'version': '2.2',
            'Timeout': 120,
            'KeepAlive': True,
            'MaxKeepAliveRequests': 100,
            'KeepAliveTimeout': 3,
            'log_level': 'warn',
            'serveradmin_mail': 'webmaster@localhost',
            'prefork': {
                'StartServers': 25,
                'MinSpareServers': 25,
                'MaxSpareServers': 25,
                'MaxClients': 150,
                'MaxRequestsPerChild': 3000
            },
            'worker': {
                'StartServers': 5,
                'MinSpareThreads': 50,
                'MaxSpareThreads': 100,
                'ThreadLimit': 100,
                'ThreadsPerChild': 50,
                'MaxRequestsPerChild': 3000,
                'MaxClients': 700
            },
            'event': {
                'AsyncRequestWorkerFactor': "4"
            },
            'register-sites': {}
        }},
        grain='default_env',
        default='dev'
    )
    # Ubuntu 13.10 is now providing 2.4 with event by default #
    if (
        grains['lsb_distrib_id'] == "Ubuntu"
        and grains['lsb_distrib_release'] >= 13.10
    ):
        apacheStepOne.update({'mpm': 'event'})
        apacheStepOne.update({'version': '2.4'})

    apacheDefaultSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.http.apache', __salt__['grains.filter_by']({
            'Debian': {
                'package': 'apache2',
                'server': 'apache2',
                'service': 'apache2',
                'mod_wsgi': 'libapache2-mod-wsgi',
                'basedir': locs['conf_dir'] + '/apache2',
                'vhostdir': locs['conf_dir'] + '/apache2/sites-available',
                'confdir': locs['conf_dir'] + '/apache2/conf.d',
                'logdir': locs['var_log_dir'] + '/apache2',
                'wwwdir': locs['srv_dir']
            },
            'RedHat': {
                'package': 'httpd',
                'server': 'httpd',
                'service': 'httpd',
                'mod_wsgi': 'mod_wsgi',
                'basedir': locs['conf_dir'] + '/httpd',
                'vhostdir': locs['conf_dir'] + '/httpd/conf.d',
                'confdir': locs['conf_dir'] + '/httpd/conf.d',
                'logdir': locs['var_log_dir'] + '/httpd',
                'wwwdir': locs['var_dir'] + '/www'
            },
        },
            grain='os_family',
            default='Debian',
            merge=apacheStepOne
        )
    )

    #
    # Pureftpd:  (services.ftp.pureftpd)
    #
    pureftpdDefaultSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.ftp.pureftpdefaults', {
            'Virtualchroot': 'false',
            'InetdMode': 'standalone',
            'UploadUid': '',
            'UploadGid': '',
            'UploadScript': '',
        }
    )
    pureftpdSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.ftp.pureftp', {
            'AllowAnonymousFXP': 'no',
            'AllowDotFiles': '',
            'AllowUserFXP': '',
            'AltLog': 'clf:/var/log/pure-ftpd/transfer.log',
            'AnonymousBandwidth': '',
            'AnonymousCanCreateDirs': 'no',
            'AnonymousCantUpload': 'yes',
            'AnonymousOnly': '',
            'AnonymousRatio': '',
            'AntiWarez': '',
            'AutoRename': '',
            'Bind': '',
            'BrokenClientsCompatibility': 'yes',
            'CallUploadScript': '',
            'ChrootEveryone': 'yes',
            'ClientCharset': '',
            'Daemonize': "",
            'DisplayDotFiles': "yes",
            'DontResolve': "yes",
            'FSCharset': 'utf-8',
            'IPV4Only': "yes",
            'IPV6Only': "",
            'KeepAllFiles': "no",
            'LimitRecursion': "5000 500",
            'LogPID': "",
            'MaxClientsNumber': "",
            'MaxClientsPerIP': "",
            'MaxDiskUsage': "90",
            'MinUID': '1000',
            'NATmode': "",
            'NoAnonymous': 'yes',
            'NoChmod': "",
            'NoRename': "",
            'NoTruncate': "",
            'Quota': "",
            'SyslogFacility': "",
            'TLS': "1",
            'TrustedGID': "",
            'TrustedIP': "",
            'Umask': "133 022",
            'UserBandwidth': "",
            'UserRatio': "",
            'VerboseLog': "yes",

            'PassiveIP': "",
            'PassivePortRange': "",

            'PAMAuthentication': 'yes',
            'UnixAuthentication': 'no',
            'PureDB': '/etc/pure-ftpd/pureftpd.pdb',
            'MySQLConfigFile': "",
            'ExtAuth': "",
            'LDAPConfigFile': "",
            'PGSQLConfigFile': "",
        }
    )
    for setting in pureftpdSettings:
        pureftpdSettings.update({setting: pureftpdSettings[setting] + '\n'})

    #
    # PostGRESQL:  (services.db.postgresql)
    # default postgresql/ grains configured databases (see service doc)
    #
    pgDbs = {}
    for dbk, data in pillar.items():
        if dbk.endswith('-makina-postgresql'):
            db = data.get('name', dbk.split('-makina-postgresql')[0])
            pgDbs.update({db: data})
    #
    # default postgresql/ grains configured users (see service doc)
    #
    postgresqlUsers = {}
    for userk, data in pillar.items():
        if userk.endswith('-makina-services-postgresql-user'):
            postgresqlUsers.update({user: data})

    #
    # default activated postgresql versions & settings:
    #
    defaultPgVersion = '9.3'
    pgSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.postgresql', {
            'user': 'postgres',
            'version': defaultPgVersion,
            'versions': [defaultPgVersion],
            'postgis': {'2.1': [defaultPgVersion, '9.2']},
            'postgis_db': 'postgis',
        }
    )
    pgVers = pgSettings['versions']
    postgisVers = pgSettings['postgis']
    postgisDbName = pgSettings['postgis_db']
    postgresqlUser = pgSettings['user']

    #
    # shorewall pillar parsing
    #
    shw_enabled = (
        __salt__['mc_utils.get'](
            'makina-states.services.shorewall.enabled', False))
    shwIfformat = 'FORMAT 2'
    if grains['os'] not in ['Debian']:
        shwIfformat = '?'
    shwPolicies = []
    shwZones = {}
    shwInterfaces = {}
    shwParams = {}
    shwMasqs = {}
    shwRules = {}
    shwDefaultState = 'new'
    shwData = {
        'interfaces': shwInterfaces,
        'rules': shwRules,
        'params': shwParams,
        'policies': shwPolicies,
        'zones': shwZones,
        'masqs': shwMasqs,
        'ifformat': shwIfformat,
    }
    for sid, shorewall in pillar.items():
        if sid.endswith('makina-shorewall'):
            shwlocrules = shorewall.get('rules', {})
            for i in shwlocrules:
                section = i.get('section', shwDefaultState).upper()
                if section not in shwRules:
                    shwRules.update({section: []})
                shwRules[section].append(i)
            shwInterfaces.update(shorewall.get('interfaces', {}))
            shwMasqs.update(shorewall.get('masqs', {}))
            shwParams.update(shorewall.get('params', {}))
            shwZones.update(shorewall.get('zones', {}))
            shwPolicies.extend(shorewall.get('policies', []))

    #
    # MySQL Fine Settings -----------------------------------------------
    # TODO: review this comment: when not in dev
    # you MUST define AT LEAST mysql-default-settings.root_passwd
    # in your PILLAR, else you'll have state failures
    #
    # * conn_[host|user|pass]: Connection settings, user/pass/host used by salt
    #                          to manage users, grants and database creations
    # * character_set: default character set on
    # CREATE DATABASE (use utf8' not 'utf-8')
    # * collate: default collate on CREATE DATABASE
    # -- my.cnf settings (or conf.d/local.cnf in fact) ---
    # * noDNS: Avoid name resolution on connections checks, must-have.
    #          This is the skip-name-resolv option
    # * memory_usage_percent: the macro will compute magiccaly the settings to
    #   fit this percentage of full memory on the host. So by default it's 50%
    #   of all RAM on a dev envirronment and 85% for a production one where
    #   the MySQl server should be alone on a server. Then all others settings
    #   parameters in the 'tunning' key could be set to False to let the macro
    #   fill the gaps. If you set somtehing other than False for one of theses
    #   settings it will be used instead of the value computed by the macro,
    #   check the macro for details and comments on all theses parameters.
    #   Note the "_M" means Mo, so for 2Go of innodb_buffer_pool_size use
    #   2024, that is 2024Mo.
    #   Tweak the 'number_of_table_indicator' to adjust some settings
    #   automatically from that, for example several Drupal instances
    #   using a lot of fields
    #   could manage several hundreds of tables. <=== IMPORTANT
    # Default OS-based paths settings added on mysqlData
    mysqlSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.db.mysql',
        __salt__['grains.filter_by'](
            {
                'Debian': {
                    'packages': {
                        'main': 'mysql-server',
                        'dev': 'libmysqlclient-dev',
                        'python': 'python-mysqldb',
                        'php': 'php-mysql'
                    },
                    'service': 'mysql',
                    'port': '5432',
                    'user': 'mysql',
                    'group': 'mysql',
                    'root_passwd': '',
                    'sharedir': locs['share_dir'] + '/mysql',
                    'datadir': locs['var_lib_dir'] + '/mysql',
                    'tmpdir': locs['tmp_dir'],
                    'etcdir': locs['conf_dir'] + '/mysql/conf.d',
                    'logdir': locs['var_log_dir'] + '/mysql',
                    'basedir': locs['usr_dir'],
                    'sockdir': locs['var_run_dir'] + '/mysqld'
                },
                'RedHat': {},
            },
            merge=__salt__['grains.filter_by'](
                {
                    'dev': {
                        'conn_host': 'localhost',
                        'myCnf': None,
                        'noautoconf': False,
                        'conn_user': 'root',
                        'conn_pass': '',
                        'character_set': 'utf8',
                        'collate': 'utf8_general_ci',
                        'noDNS': True,
                        'isPercona': False,
                        'isOracle': True,
                        'isMariaDB': False,
                        'memory_usage_percent': 15,
                        'nb_connections': 25,
                        'innodb_buffer_pool_size_M': False,
                        'query_cache_size_M': False,
                        'innodb_buffer_pool_instances': False,
                        'innodb_log_buffer_size_M': False,
                        'innodb_flush_method': 'O_DSYNC',
                        'innodb_thread_concurrency': False,
                        'sync_binlog': False,
                        'innodb_flush_log_at_trx_commit': 0,
                        'innodb_additional_mem_pool_size_M': False,
                        'tmp_table_size_M': False,
                        'number_of_table_indicator': 500
                    },
                    'prod': {
                        'myCnf': None,
                        'noautoconf': False,
                        'conn_host': 'localhost',
                        'conn_user': 'root',
                        'conn_pass': '',
                        'character_set': 'utf8',
                        'collate': 'utf8_general_ci',
                        'noDNS': True,
                        'isPercona': False,
                        'isOracle': True,
                        'isMariaDB': False,
                        'mysql.cnf': None,
                        'memory_usage_percent': 85,
                        'nb_connections': 250,
                        'innodb_buffer_pool_size': False,
                        'query_cache_size_M': False,
                        'innodb_buffer_pool_instances': False,
                        'innodb_log_buffer_size_M': False,
                        'innodb_flush_method': 'O_DIRECT',
                        'innodb_thread_concurrency': False,
                        'sync_binlog': False,
                        'innodb_flush_log_at_trx_commit': 2,
                        'innodb_additional_mem_pool_size_M': False,
                        'tmp_table_size_M': False,
                        'number_of_table_indicator': 1000
                    },
                },
                grain='default_env',
                default='dev'
            ),
            grain='os_family'
        )
    )

    # ----------------------------------------------------
    # MySQL default custom configuration (services.db.mysql)
    # To override the default makina-states configuration file,
    # Use the 'makina-states.services.mysql.cnf pillar/grain
    #
    myCnf = mysqlSettings['myCnf']
    # Set this to true to disable mysql automatic configuration
    # (if you want to call the mysql macros yourself
    # (makina-states.services.mysql.noautoconf)
    #
    myDisableAutoConf = mysqlSettings['noautoconf']

    #
    # DB_SMART_BACKUP
    #
    dbsmartbackupSettings = __salt__['mc_utils.defaults'](
        'makina-states.services.backup.db_smart_backup', {
            'cron_minute': '1',
            'backup_path_prefix': locs['srv_dir'] + '/backups',
            'cron_hour': '1',
            'dbexclude': '',
            'dbnames': 'all',
            'disable_mail': '',
            'global_backup': '1',
            'group': 'root',
            'keep_days': '14',
            'keep_lasts': '24',
            'keep_logs': '60',
            'keep_monthes': '12',
            'keep_weeks': '8',
            'mail': 'root@localhost',
            'mysqldump_autocommit': '1',
            'mysqldump_completeinserts': '1',
            'mysqldump_debug': '',
            'mysqldump_locktables': '',
            'mysqldump_noroutines': '',
            'mysqldump_no_single_transaction': '',
            'mysql_password': mysqlSettings['root_passwd'],
            'mysql_sock_paths': mysqlSettings['sockdir'] + '/mysqld.sock',
            'mysql_use_ssl': '',
            'owner': 'root',
            'servername': grains['fqdn'],
        }
    )
    return locals()


def settings():
    REG = get_reg()
    ret = REG.setdefault('settings', _settings(REG))
    set_reg(REG)
    return ret


def _registry(REG):
    settings = __salt__['mc_{0}.settings'.format(__name)]()
    REG['registry'] =  __salt__[
        'mc_macros.construct_registry_configuration'
    ](settings, defaults={
        'backup.bacula-fd': {'active': False},
        'backup.dbsmartbackup': {'active': False},
        'base.ntp': {'active': settings['ntpEn']},
        'base.ssh': {'active': True},
        'db.mysql': {'active': False},
        'db.postgresql': {'active': False},
        'firewall.shorewall': {'active': False},
        'ftp.pureftpd': {'active': False},
        'gis.postgis': {'active': False},
        'gis.qgis': {'active': False},
        'http.apache': {'active': False},
        'java.solr4': {'active': False},
        'java.tomcat7': {'active': False},
        'mail.dovecot': {'active': False},
        'mail.postfix': {'active': False},
        'php.common': {'active': False},
        'php.modphp': {'active': False},
        'php.phpfpm': {'active': False},
        'php.phpfpm_with_apache': {'active': False},
        'virt.docker': {'active': False},
        'virt.docker-shorewall': {'active': False},
        'virt.lxc': {'active': False},
        'virt.lxc-shorewall': {'active': False},
        'mastersalt_minion': {'active': False},
        'mastersalt_master': {'active': False},
        'mastersalt': {'active': False},
        'salt_minion': {'active': False},
        'salt_master': {'active': False},
        'salt': {'active': False},
    })


def registry():
    REG = get_reg()
    ret = REG.setdefault('registry', _registry(REG))
    set_reg(REG)
    return ret


if (
    __name__ == '__main__'
    and os.environ.get('makina_test', None) == 'mc_utils'
):
    unittest.main()
