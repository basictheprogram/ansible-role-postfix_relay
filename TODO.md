# TODO

Flagged during the 2026-09-23 `ansible-sync-role` pass, not fixed in
that session. Not a general backlog — see `CLAUDE.md`'s "Settled
decisions" for everything that *was* decided/fixed.

* **`vars/Debian.yml` package names are unverified against real
  Debian trixie apt repos.** They're currently a straight copy of
  `vars/Ubuntu.yml`'s list (`postfix`, `postfix-pcre`, `make`,
  `dovecot-core`, `dovecot-sqlite`, `sqlite3`) — molecule tests this
  via the `geerlingguy/docker-debian13-ansible` image, but hasn't been
  confirmed against a real Debian trixie host outside CI.
