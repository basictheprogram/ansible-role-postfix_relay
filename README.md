# Role Name #
Postfix with smtp-tls and smtp-auth as a smtp relay.

# Requirements #
Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

# Role Variables #
```
postfix_admin_email: "user@domain.com"

# git or template
postfix_configuration: "template"

postfix_myhostname: "smtp.domain.com"
postfix_myorigin: "smtp.domain.com"
postfix_mynetworks: 
    - "192.168.100.0/24"
    - "10.10.10.0/24"
   
postfix_mydestination: "smtp.domain.com, smtp2.domain.com"
postfix_inet_protocols: ipv4
postfix_compatibility_level: 2
postfix_sasl_type: dovecot
postfix_tls_rsa: true

postfix_ports: 
    - 10025
```

# Dependencies #
A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

# Example Playbook #
````
- hosts: servers
  roles:
     - { role: postfix-relay, become: yes }
```

# User Management #
Quick tutorial on how to add users to the sqlite database for smtp-auth relay access

## Add user ##
Create SHA512 encrpted password with the doveadm tool
```
relay$ doveadm pw -s SHA512-CRYPT
Enter new password:
Retype new password:
{SHA512-CRYPT}XXXX
```

Insert the user into the sqlite database. The home, uid, gid are not used at this time.
```
relay$ sudo -i
root@relay:~# cd /etc/dovecot/
root@relay:/etc/dovecot# sqlite3 auth-db.db
sqlite> insert into users (userid, domain, password, home, uid, gid) values ('user','domain','{SHA512-CRYPT}XXX','home',1000,1000);
sqlite> .exit
```

## Update User ##
Change users password. Create SHA512 encrpted password with the doveadm tool
```
relay$ doveadm pw -s SHA512-CRYPT
Enter new password:
Retype new password:
{SHA512-CRYPT}XXX

relay$ sudo -i
root@relay:~# cd /etc/dovecot/
root@relay:/etc/dovecot# sqlite3 auth-db.db
sqlite> update users set password='{SHA512-CRYPT}XXX' where userid='user' and domain='domain' ;
sqlite> .exit
```

# License #


# Author Information #
[Real Time Enterprises Inc.](http://www.real-time.com), 
[Bob Tanner](https://github.com/basictheprogram)