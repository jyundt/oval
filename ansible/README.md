# The Oval App
## Ansible Deploy Overview
The server deployment uses Ansible for the three application components:
* DB (Postgres)
* Application Server (uWSGI)
* Web Server (Apache)

The ansible playbook(s) are written for RHEL7 based distributions (CentOS, SciLi, etc), but it probably wouldn't be too hard to extend the playbooks for Debian based distros.

## Roles/Profiles
The three application components are divided in Ansible roles:
* [db](roles/db)
* [app](roles/app)
* [web](roles/web)




A sample [playbook](single-host.yml) is included as an example. This playbook configures all three services to run on one host.

Sensitive information (http private keys, application API keys) are stored in ansible-vault files in their respective roles directory.

Sever specific configuration items are included in: `roles/TARGETROLE/vars/SERVERHOSTNAME`

As an example, the http certs and keys for test.theoval.us are stored in [roles/web/vars/test.theoval.us.yml](roles/web/vars/test.theoval.us.yml)


## Usage
The sample single-host.yml playbook will prompt for the hostname or IP of the target server. Additionally, you will need to specify `--ask-pass` if password-less SSH for root is **not** configured.

Example usage
```
[user@ansible-client ansible]$ ansible-playbook single-host.yml --ask-pass --ask-vault
SSH password: 
Vault password: 
target hostname or IP: test.theoval.us

PLAY [localhost] ***************************************************************

TASK [add_host] ****************************************************************
changed: [localhost]

PLAY [deploy] ******************************************************************

TASK [setup] *******************************************************************
ok: [test.theoval.us]
.
.
.
```
## Limitations
* The ansible scripts do not populate the DB with any data (e.g. admins, races, riders, etc), WIP
* A manual reboot might be required if SELinux is flipped from `disabled` to `enforcing`
* Flask-Migrate migrations/upgrades are not properly handled. Manual intervention is required when a schema update occurs.

