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
```
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
root@relay:~# cd /etc/postfix/
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

## Mail From verification ##
The smtp authentication username must match the "Mail From". 
```
Mail from tanner@real-time.com = smtp authentication username "tanner@real-time.com". 
```
If they do not match an entry must be put into the /etc/postfix/login_map (see 
http://www.postfix.org/postconf.5.html#smtpd_sender_login_maps). 

## Self-sign Certificate ##
You will need to accept the self-signed certificate for TLS to work as expected.
```
Issued To
Common Name (CN)          relay.dmz.example.com
Organization (O)          Real Time Enterprises Inc
Organization Unit (OU)    Real Time Support
Serial Number             78:39:23:A8

Issued by
Common Name (CN)          Postfix Certificate Authority
Organization (O)          Real Time Enterprises Inc
Organization Unit (OU)    Real Time Support

Period of Validity
Begins On                 Friday, January 27, 2017
Expires On                Monday, January 25, 2027

Fingerprints
SHA-256 Fingerprint       9D:93:71:A4:89:A0:EE:44:08:F2:C2:7E:FF:0D:6F:1E:
                          18:1F:E4:E5:E7:6C:A2:BF:B3:0C:B0:7E:B4:E4:27:86
SHA1 Fingerprint          19:CE:F7:E6:8C:9F:98:FC:73:54:2D:BB:37:92:29:FD:55:FC:42:3E
```

## mynetworks ##
Need to edit the [mynetworks](http://bit.ly/2jb9ZVB) file?

## relay_domains ##
Need to edit the [relay_domains](http://bit.ly/2jb9ZVB) file?

# License #


# Author Information #
[Real Time Enterprises Inc.](http://www.real-time.com), 
[Bob Tanner](https://github.com/basictheprogram)