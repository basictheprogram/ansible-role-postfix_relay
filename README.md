# postfix_relay

Configures Postfix as an SMTP relay, with optional Dovecot SASL
authentication and TLS via Let's Encrypt (`geerlingguy.certbot`).
`main.cf` can be sourced from this role's own template, or left to a
host that manages its own Postfix config (see `postfix_configuration`
below).

# Requirements #

* Ansible core >= 2.20
* For `postfix_conf.tls_rsa: lets_encrypt`: the `geerlingguy.certbot`
  role, declared in `requirements.yml`; install with
  `ansible-galaxy role install -r requirements.yml`.

# Supported Platforms #

Debian (trixie) and Ubuntu (jammy, noble, resolute).

# Role Variables #

## Top-level variables ##

| Variable | Required | Description |
|---|---|---|
| `postfix_configuration` | yes | One of `template` or `localhost`. See Task Flow below. |
| `postfix_ports` | no | List of additional TCP ports Postfix should listen on. |
| `postfix_aliases` | no | List of `{user, alias}` entries appended to `/etc/aliases`, beyond the built-in `postmaster`/`root` lines. |
| `postfix_conf` | when `postfix_configuration: template` | Dict of Postfix configuration values — see below. Ignored for the other two modes. |

## `postfix_conf` (when `postfix_configuration: template`) ##

| Key | Required | Default | Description |
|---|---|---|---|
| `admin_email` | yes | — | Delivery address for the `root` alias. |
| `myhostname` | yes | — | Postfix `myhostname`. |
| `myorigin` | yes | — | Postfix `myorigin`. |
| `mydestination` | yes | — | Postfix `mydestination` (this role always appends `, localhost`). |
| `inet_interfaces` | no | `all` | Postfix `inet_interfaces`. |
| `inet_protocols` | no | `all` | Postfix `inet_protocols`. |
| `compatibility_level` | no | `3` | Postfix `compatibility_level`. |
| `message_size_limit` | no | `10240000` | Postfix `message_size_limit`, in bytes. |
| `masquerade_domains` | no | — | If set, enables `masquerade_domains` and `local_header_rewrite_clients`. |
| `mynetworks` | no | — | A list of CIDR entries (when `mynetworks_conf` is `list`, the default) or a source file path (when `mynetworks_conf: file`). |
| `mynetworks_conf` | no | `list` | `list` or `file` — selects how `mynetworks` is interpreted. |
| `relay_domains` | no | — | Source file path copied to `/etc/postfix/relay_domains`. Only takes effect when `relay_domains_conf: file` — there is no list-based mode. |
| `relay_domains_conf` | no | — | Must be `file` for `relay_domains` to take effect. |
| `sasl_type` | no | — | Set to `dovecot` to enable Dovecot SASL authentication. |
| `tls_rsa` | no | — | `lets_encrypt` (the only working option — see Known limitations) or `self-signed` (documented but non-functional). |
| `smtpd_tls_security_level` | no | `may` | Postfix `smtpd_tls_security_level`. |
| `smtpd_tls_loglevel` | no | `1` | Postfix `smtpd_tls_loglevel`. |

The full schema is also machine-readable in `meta/argument_specs.yml`,
which Ansible validates automatically before this role's own tasks run.

## OS-specific variables (`vars/`) ##

`vars/Ubuntu.yml` and `vars/Debian.yml` each set `postfix_relay_packages`
(the package list installed on that OS family). These are loaded
automatically via `include_vars` and are not meant to be overridden by
consumers in the normal sense.

# Task Flow #

1. **Preflight** (`tasks/preflight.yml`) — runs first, before anything
   else. Checks: ansible-core version, supported OS family,
   `mynetworks_conf: file`/`relay_domains_conf: file`'s cross-field
   requirements, and rejects `tls_rsa: self-signed` outright (see
   Known limitations). `postfix_configuration`'s and `postfix_conf`'s
   own required-ness/types/choices are validated separately and
   automatically via `meta/argument_specs.yml`.
2. Load OS-specific variables from `vars/`.
3. On Debian-family hosts: install packages.
4. Deploy `/etc/postfix` per `postfix_configuration`:
   `template` renders `main.cf` from this role's template;
   `localhost` is a no-op placeholder for hosts managing their own config.
5. Configure `/etc/aliases`.
6. Add any `postfix_ports` to `master.cf`.
7. If `postfix_conf.sasl_type: dovecot`, configure Dovecot SASL
   authentication (SQLite-backed user database).
8. If `postfix_conf.tls_rsa: lets_encrypt`, run `geerlingguy.certbot`.

# Known limitations #

* **`postfix_conf.tls_rsa: self-signed` does not work standalone.**
  It imports `{{ role_path }}/../lib/gnutls-certs.yml`, a file that
  only exists in the old monorepo this role was extracted from.
  Preflight rejects this value outright with a clear message. Use
  `lets_encrypt` instead. See `CLAUDE.md` for the full history.

# Example Playbook #

```yaml
- hosts: servers
  roles:
    - role: postfix_relay
      become: true
  vars:
    postfix_configuration: template
    postfix_conf:
      admin_email: admin@example.com
      myhostname: smtp.example.com
      myorigin: example.com
      mydestination: "smtp.example.com, smtp2.example.com"
      mynetworks:
        - "192.168.100.0/24"
        - "10.10.10.0/24"
      sasl_type: dovecot
      tls_rsa: lets_encrypt
    postfix_ports:
      - 10025
```

# User Management #

Quick tutorial on how to add users to the SQLite database for
SMTP-auth relay access.

## Add user ##

Create a SHA512-encrypted password with the `doveadm` tool:

```
relay$ doveadm pw -s SHA512-CRYPT
Enter new password:
Retype new password:
{SHA512-CRYPT}XXXX
```

Insert the user into the SQLite database. `home`, `uid`, `gid` are not
used at this time.

```
relay$ sudo -i
root@relay:~# cd /etc/postfix/
root@relay:/etc/dovecot# sqlite3 auth-db.db
sqlite> insert into users (userid, domain, password, home, uid, gid) values ('user','domain','{SHA512-CRYPT}XXX','home',1000,1000);
sqlite> .exit
```

## Update user ##

Change a user's password. Create a SHA512-encrypted password with the
`doveadm` tool:

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

The SMTP authentication username must match the "Mail From" address:

```
Mail from tanner@example.com = smtp authentication username "tanner@example.com".
```

If they don't match, an entry must be added to
`/etc/postfix/login_map` (see
[`smtpd_sender_login_maps`](http://www.postfix.org/postconf.5.html#smtpd_sender_login_maps)).

## mynetworks ##

Set `postfix_conf.mynetworks` to a list of CIDR entries (the default
mode), or to a source file path with `postfix_conf.mynetworks_conf:
file` — see Role Variables above.

## relay_domains ##

Set `postfix_conf.relay_domains` to a source file path along with
`postfix_conf.relay_domains_conf: file` — see Role Variables above.
There is no list-based mode for `relay_domains`.

# License #

MIT

# Author Information #

[Real Time Enterprises Inc.](http://www.real-time.com),
[Bob Tanner](https://github.com/basictheprogram)
