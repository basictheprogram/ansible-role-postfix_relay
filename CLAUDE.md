# Claude Code project notes — postfix_relay

Installs and configures Postfix as an SMTP relay: SASL authentication
via Dovecot, TLS via either a self-signed certificate (`certtool`) or
Let's Encrypt (`geerlingguy.certbot`), and `main.cf` sourced from one
of three modes (`postfix_configuration`: `template`, `git`, or
`localhost`).

---

## Behavioral guidelines

These four rules govern how to work in this repo. They bias toward
caution over speed — for trivial one-liner changes, use judgment.

### 1. Think before writing tasks

**Don't assume. Surface tradeoffs. Ask when uncertain.**

Before adding or changing anything:

* State assumptions explicitly. If a variable could live in `defaults/`,
  `vars/`, or `host_vars`, say which and why before choosing.
* If multiple approaches exist (e.g. `ansible.builtin.command` vs a
  purpose-built module), present the tradeoff — don't pick silently.
* If the request is ambiguous (which task file? which template block?),
  name the ambiguity and ask. Don't guess and implement.
* If a simpler approach solves the problem, say so and push back.
* If something conflicts with `DESIGN.md`, flag it before proceeding.

### 2. Simplicity first

**Minimum tasks, variables, and template logic that solve the problem.**

* No new default variables beyond what the task being added requires.
* No Jinja2 abstraction for logic used in only one template.
* No `when:` conditions for scenarios that have no test coverage.
* No "future-proofing" of the public interface that wasn't asked for.
* If a template block is 30 lines and could be 10, rewrite it.

Ask: would a senior Ansible engineer call this overcomplicated? If yes,
simplify.

### 3. Surgical changes

**Touch only what the request requires. Clean up only your own mess.**

When editing existing tasks, templates, or defaults:

* Don't reformat adjacent YAML, fix unrelated comments, or clean up
  upstream code that wasn't broken by your change.
* Match the existing style — indentation, quoting, bullet character —
  even if you'd do it differently from scratch.
* If you notice unrelated dead code or stale variables, mention it;
  don't delete it without being asked.

When your change creates orphans:

* Remove `vars`, `when` conditions, or template blocks that YOUR change
  made unreachable.
* Don't remove pre-existing orphans unless explicitly asked.

Every changed line should trace directly to the request.

### 4. Goal-driven execution

**Define the success criteria before starting. Verify before declaring done.**

Transform requests into verifiable outcomes:

* "Add a preflight assertion" → `molecule converge` passes,
  `molecule verify` passes, `pre-commit run --all-files` is clean.
* "Fix an idempotency bug" → second `molecule converge` reports zero
  changed tasks.
* "Refactor a template" → rendered output is byte-for-byte identical
  to pre-refactor output on a converged instance.

For multi-step changes, state a brief plan before starting:

    1. Edit template → verify: rendered YAML is valid
    2. Add task       → verify: molecule converge green
    3. Add test       → verify: molecule verify green
    4. Lint           → verify: pre-commit run --all-files clean

Strong success criteria allow independent verification. Weak criteria
("make it work") require constant clarification.

---

## Role-specific notes

### Source of truth

`DESIGN.md` is the authoritative spec. Read it before any non-trivial
change. If code disagrees with `DESIGN.md`, `DESIGN.md` is right —
flag the discrepancy and ask before fixing the design to match the code.

### Design notes

No DESIGN.md found — add one.

### Secrets

Role-specific secret variable names:

* `key_pem` / `ca_key_pem` — paths to the TLS private key and CA
  private key used to generate the self-signed certificate via
  `certtool` (sourced from the consumer's `master_ca_pem`/
  `master_ca_key_pem` dicts, keyed on `'postfix'`).
* `dovecot_sql_db` — the SQLite database file holding Dovecot SASL
  users' password hashes once generated on the target host.
  `files/auth-db.sql` (the schema shipped in this repo) has no real
  credentials in it — only column definitions.

### Commit scopes

Role-specific subsystem scopes: `conf` (`tasks/conf/*`), `dovecot`
(`tasks/dovecot/*`), `tls` (`tasks/tls/*`), `debian`.

### Settled decisions

* Added `LICENSE` (MIT, Real Time Enterprises, Inc., 2026) — closes
  the gap `meta/main.yml`'s `license: MIT` (Step 5) left open.
* Removed the `postfix_configuration: git` mode entirely (2026-09-23):
  `tasks/conf/remote-git.yml`, the `postfix_repository`/
  `postfix_branch` variables (and their `argument_specs.yml` entries
  and preflight assertion), the `git` choice from
  `postfix_configuration`'s `argument_specs.yml` choices, and the
  now-orphaned `Rebuild db` handler (only ever notified by the removed
  git-clone task). Updated README and `meta/argument_specs.yml`
  accordingly. `postfix_configuration` now has two modes, not three.
* `tasks/tls/main.yml`'s `postfix_conf.tls_rsa: self-signed` path
  imports `{{ role_path }}/../lib/gnutls-certs.yml`, an old monorepo
  pattern that only exists at `legacy/roles/lib/gnutls-certs.yml` —
  there is no `../lib` sibling next to this standalone repo. Decided
  (2026-09-23) to document this as broken rather than fix or remove
  it, matching the identical precedent in
  `ansible-role-backuppc_server`'s `tasks/self_signed_ssl.yml`.
  Self-signed TLS provisioning is **not a working feature of this
  role as checked out standalone** — don't describe it as one in the
  README (Step 8), and don't spend time re-diagnosing "why does the
  self-signed path fail" as a new bug if it resurfaces. Reinforcing
  finding (Step 4): `templates/main_cf.j2` renders
  `smtpd_tls_cert_file`/`smtpd_tls_key_file` pointing at
  `/etc/letsencrypt/live/...` unconditionally whenever
  `postfix_conf.tls_rsa` is defined at all — it was never made
  conditional on `tls_rsa`'s actual value, so even if the missing
  `gnutls-certs.yml` import were fixed, `self-signed` would still
  render the wrong cert paths. `lets_encrypt` is the only `tls_rsa`
  value that is actually wired end-to-end today. Removed the orphaned
  `templates/certtool.cfg.j2` (only ever consumed by the missing
  `gnutls-certs.yml`) as part of the same decision.
* Removed a stray unconditional `ansible.builtin.debug` task from
  `tasks/conf/template.yml` (dumped `postfix_conf.mynetworks_conf`,
  no apparent purpose — troubleshooting cruft never cleaned up).
* Wired in the previously commented-out "Configure mynetworks (list)"
  task in `tasks/conf/template.yml` as the default mode (runs
  whenever `postfix_conf.mynetworks_conf` is unset or anything other
  than `'file'`) — added a `| default('list')` guard the original
  commented block didn't have, since without it any consumer who
  doesn't set `mynetworks_conf` at all (the likely common case) would
  hit an undefined-attribute error on the bare `!=` comparison. This
  is a behavior change for any existing consumer relying on
  `postfix_conf.mynetworks` silently doing nothing when
  `mynetworks_conf` isn't `'file'` — they will now get mynetworks
  lines written via `lineinfile`.
* Removed the commented-out "Configure login_map (file)" task in the
  same file — dead code for a feature (`postfix_conf.login_map` as a
  file source) with no corresponding default, template, or
  documentation anywhere else in the role.
* `meta/main.yml` (2026-09-23): dropped `platforms:` entirely (see
  Step 5's rationale, not repeated here), bumped
  `min_ansible_version` to `"2.20"`, and settled the supported
  platform list as Debian (trixie) and Ubuntu (jammy, noble,
  resolute) — dropped bionic/xenial (untracked, years past EOL) and
  focal (EOL 2025-05-31). Debian support is new as of this decision,
  not carried over from before — added `vars/Debian.yml` (identical
  package list to `vars/Ubuntu.yml`) to make it real rather than just
  a documentation claim. Package name compatibility with real Debian
  trixie apt repos hasn't been verified outside molecule CI (same
  caveat as `ansible-role-backuppc_server`'s Debian addition).
* `license: MIT` (was the garbled placeholder `"license (BSD, MIT)"`)
  — decided 2026-09-23 despite no `LICENSE` file existing in this repo
  yet; a `LICENSE` file still needs to be added separately to match.
* **Scrubbed a leaked customer domain from this repo's entire git
  history** (2026-09-23), not just the working tree fix in `converge.yml`
  (Step 10). It was introduced in the commit "Refactor postfix
  configuration to match the postfix satellite role", already pushed
  to `origin` (`gitlab.real-time.com/ansible-roles/postfix_relay.git`)
  on both `ansible-5.9` and `ansible-core-2.20`. Used `git filter-repo
  --replace-text` to replace it with a placeholder across every commit
  on every local ref, then force-pushed both affected branches with
  `--force-with-lease` after confirming no one had pushed to them
  since the last fetch — this rewrote every commit hash on both
  branches. Verified zero remaining occurrences across
  `origin/master`/`origin/ansible-5.9`/`origin/ansible-core-2.20`
  afterward. If anyone else has either branch checked out, they need
  to re-clone or hard-reset to the new history rather than pull.
* Removed `vars/default.yml` (2026-09-23) — its content was a full
  duplicate of `vars/main.yml`, not genuinely OS-specific, and
  `vars/main.yml` is auto-loaded by Ansible regardless of the
  `first_found` lookup. Also removed the dead `"default.yml"` entry
  from `tasks/main.yml`'s `first_found` `files:` list.
* Every file under `molecule/default/tests/` (including `__init__.py`)
  needs a `# Copyright (c) 2026 Real Time Enterprises, Inc.` first
  line — `ruff.toml`'s `select = ["ALL"]` includes `CPY001`, which
  fails on any Python file missing this. Matches the convention
  already established in `ansible-role-backuppc_server`'s test suite.
* Added `tasks/preflight.yml`, wired in as the very first task (ahead
  of even `include_vars`, since this role builds nothing dynamic
  before touching the host). Kept it deliberately narrow: since
  `meta/argument_specs.yml` (Step 4) already auto-validates
  `postfix_configuration`'s required-ness/choices and `postfix_conf`'s
  required sub-keys at role-invocation time (ansible-core has done
  this automatically for the `main` entry point since 2.11), preflight
  only covers what argument_specs *can't* express: the target host's
  OS family, cross-field conditionals
  (`postfix_configuration: git` requiring `postfix_repository`/
  `postfix_branch`; `mynetworks_conf: file` requiring `mynetworks` be
  set; `relay_domains` being silently ignored without
  `relay_domains_conf: file`), and a hard fail-fast on
  `tls_rsa: self-signed` (already documented as non-functional
  standalone — preflight now catches it immediately instead of
  failing deep inside `tasks/tls/main.yml`). Removed the now-redundant
  ad-hoc `"Check for postfix_configuration"` `fail` task from
  `tasks/main.yml` — argument_specs already covers it, more
  thoroughly (choices, not just definedness).

### Open questions

If a task touches one of these, leave a `# TODO(open-q):` comment:

* `postfix_configuration: git` mode is not covered by molecule tests.
  It's straightforward to fixture-test (a plain target-side git clone,
  no `delegate_to: localhost` control-node dependency like some other
  roles' git-deploy paths) but would need a second molecule scenario,
  since a single converge run can't cleanly exercise two
  mutually-exclusive `postfix_configuration` modes on one host.
  Decided (2026-09-23) to defer rather than add scope to this sync —
  revisit if this mode gets real production use.

### Implementation order

Work one section at a time. Each item = one focused session and one
commit. Stop and verify between items.

1. Step 3 — ansible-core 2.20 compliance: done (2026-09-23).
   `tasks/main.yml`'s `ansible_distribution_release`/
   `ansible_distribution`/`ansible_os_family` references converted to
   `ansible_facts['...']`. The `include_vars`/`first_found` `paths:`
   already pointed at `vars`. The stray debug task and dead
   `login_map` block were removed, and "Configure mynetworks (list)"
   was wired in as the default mode — see Settled decisions for all
   three. Still open: the `lets_encrypt` `tls_rsa` path's
   `include_role: geerlingguy.certbot` is not declared anywhere as a
   dependency (no `requirements.yml`, empty `meta/main.yml`
   `dependencies: []`) — it will fail "role not found" for any
   consumer who picks that path today. Deferred to Step 13 (adding a
   role-root `requirements.yml`), not fixed here.
2. Step 4 — lint clean: run after Step 3. `meta/argument_specs.yml`
   doesn't exist yet — add one documenting `postfix_configuration` and
   `postfix_conf`'s keys. Check `files`/`templates` tasks for explicit
   `mode:`.
3. Step 5 — refactor `meta/main.yml`: done (2026-09-23). See Settled
   decisions for the platform list, license, and `vars/Debian.yml`
   addition. `min_ansible_version` bumped to `"2.20"`,
   `author`/`namespace`/`company` set, `platforms:` key removed,
   `issue_tracker_url` set from `git remote -v`
   (`gitlab.real-time.com/ansible-roles/postfix_relay/-/issues`),
   `galaxy_tags` expanded beyond `linux`/`ubuntu`.
4. Step 5b — LICENSE: done (2026-09-23). `LICENSE` file added — see
   Settled decisions.
5. Step 6 — `defaults/`/`vars/` split: done (2026-09-23).
   `defaults/main.yml` was already effectively empty — nothing to
   migrate, since the role's whole interface is the consumer's
   `postfix_conf` dict, not per-OS defaults. Removed `vars/default.yml`
   entirely — none of its content (`certtool`, `key_pem`,
   `dovecot_sql_*`, etc.) actually varied by OS, so it was pure
   duplication of `vars/main.yml` (which is auto-loaded regardless).
   Also dropped the now-dead `"default.yml"` entry from
   `tasks/main.yml`'s `first_found` list — `Ubuntu.yml`/`Debian.yml`
   already match for every currently-supported OS, and an unsupported
   OS will now get a clear preflight failure (Step 7) instead of
   silently loading a meaningless fallback file.
6. Step 7 — add `tasks/preflight.yml`: done (2026-09-23). See Settled
   decisions for what it covers and why it's narrower than a typical
   preflight (argument_specs already does most of the work).
7. Step 8 — update README: done (2026-09-23). Full rewrite — the old
   "Role Variables" section documented flat `postfix_*` vars that
   haven't matched the code in years (the real interface is the
   `postfix_conf` dict). Removed the "Self-sign Certificate" section
   entirely — it embedded a real production certificate's hostname
   (`relay.dmz.example.com`), serial number, and fingerprint to
   document a feature (self-signed TLS) already established as
   non-functional standalone. Kept the User Management / Mail From /
   mynetworks / relay_domains sections (still accurate), genericized
   the Mail From example's real email address.
8. Step 9 — molecule.yml: done (2026-09-23). Added `ubuntu-noble`,
   `ubuntu-resolute`, and `debian-trixie` alongside the existing jammy
   platform, matching Step 5's settled platform list. Renamed
   instances from the old `postfix-relay-molecule-jammy-instance` to
   the fleet's `<os>-<codename>` convention (`ubuntu-jammy`, etc.) and
   fixed all the non-standard capitalized values (`Galaxy`/`Docker`/
   `Ansible`/`Testinfra` → lowercase). Switched to the template's
   testinfra verifier block and dropped the `lint:` key. Updated
   `provisioner.inventory.host_vars`' key from
   `postfix-relay-molecule-jammy-instance` to `ubuntu-jammy` to match
   the rename — otherwise my own renaming would have silently orphaned
   that `tweak_motd: true` setting.
9. Step 10 — converge.yml: done (2026-09-23). Replaced
   `masquerade_domains` (previously a real-looking external customer
   domain, not reproduced here — see the git history warning in Open
   questions) with `masquerade.molecule.local`. Fixed a stray
   `myhostname: Molecule.local` capitalization (inconsistent with the
   surrounding all-lowercase `molecule.local` values — looked like
   collateral damage from the `ansible-5.9` branch's blanket
   task/handler capitalization pass accidentally touching a data
   value). Removed the unused `bootstrap_fqdn` var — it only ever fed
   the dead self-signed TLS path's cert paths, and this fixture
   doesn't set `tls_rsa` at all. Added the OS-family-aware cache-update
   `pre_tasks` from the shared asset. Decided (see below) to keep
   testing only `postfix_configuration: template`; the `git` mode
   remains untested — see Open questions.
10. Step 11 — fixtures: done, nothing further needed (2026-09-23). No
    `molecule/default/group_vars/` exists; `converge.yml`'s vars are
    already inline and the one real fixture issue (a leaked customer
    domain in `masquerade_domains`) was already fixed in Step 10.
    `prepare.yml` only installs generic utility packages. This role
    has no user/SSH-key concept, so that anonymization pattern doesn't
    apply.
11. Step 12 — testinfra suite: done (2026-09-23). Removed the unfilled
    `molecule/default/verify.yml` placeholder entirely — the
    `testinfra` verifier (Step 9) never invokes it, so it was already
    dead weight (and the source of the last remaining ansible-lint
    violation). Added `molecule/default/tests/`: skipped the
    `CONFIG_DIR_BY_FAMILY` fixture pattern (this role has no
    OS-varying config path, and its config files span two directories
    — `/etc/postfix` and `/etc/aliases`), using full absolute paths in
    `CONFIG_FILES` instead. `test_config.py` covers
    existence/permissions only; `test_postfix.py` covers rendered
    `main.cf`/`mynetworks`/`aliases` content (matched against
    `converge.yml`'s actual fixture values) plus `postfix` service
    state. Found and fixed one more trivial bug while writing the
    content assertions: `main_cf.j2`'s `inet_interfaces` line had a
    stray double space. `ansible-lint` now reports zero violations
    (`production` profile).
12. Step 13 — done (2026-09-23). Added `molecule/requirements.txt`
    (from the shared asset). No collection modules are used anywhere
    in this role (everything is `ansible.builtin`), so no
    `collections:` entry was needed — but added a role-root
    `requirements.yml` declaring `geerlingguy.certbot` under `roles:`
    (a standalone Galaxy role, not a collection module), closing the
    Step 3 dependency gap. Updated the README's Requirements and Known
    limitations sections accordingly — the "not yet declared as a
    dependency" caveat no longer applies. No `INSTALL.rst` exists in
    this role, so nothing to update there.

### Consumer side notes

<!-- TODO: fill in consumer notes -->

---

## Conventions

* **Commits**: follow the commit message guide in this file exactly.
  Conventional Commits, imperative mood, bodies wrapped at 72,
  asterisk bullets.
* **Lint**: `.ansible-lint`, `.yamllint`, `.pre-commit-config.yaml`
  define the rules. Run `pre-commit run --all-files` before declaring
  work done.
* **Secrets**: never write a credential into a tracked file. Vault
  secrets are consumed on the consumer side; the role templates them
  into config files with restricted permissions. Use `no_log: true`
  on any task that touches them.
* **Modules**: prefer FQCNs (`ansible.builtin.template`, etc.).
  The `.ansible-lint` rules require it.
* **Idempotency**: every task should be safe to re-run.

## Testing locally

* `pre-commit run --all-files` — fast lint/format pass. Run before
  every commit.
* `molecule converge` then `molecule verify` — fast iteration during
  template / task work; skips the destroy/create cycle.
* `molecule test` — full role exercise per platform. Slow; run
  before declaring a change done.

## When in doubt

Read `DESIGN.md`, then ask. The schemas and decisions there are
load-bearing.

---

## Commit message guide

You are an expert DevOps engineer and professional git commit message
writer. When generating a commit message, follow these steps exactly.

### Step 1 — Retrieve changes

Run:

    git diff --cached

Analyze the full staged diff. This is the **single source of truth**
for what will be committed.

### Step 2 — Understand the change

Determine:

* The **primary purpose** of the change
* The **type of change** (feature, bug fix, refactor, etc.)
* The **most relevant scope** within the role
* Whether the change introduces a **breaking change** for role consumers
* Whether multiple changes should be summarized together

Pay special attention to:

* Changes to `defaults/main.yml` — these define the role's public interface
* Changes to handler names, task names, and tags — consumers may pin to them
* Changes to template variables that consumers override
* Changes to config or env file templates that affect service behavior
* Changes to `meta/main.yml` — galaxy metadata, min Ansible version, platforms

If multiple files are modified, identify the **dominant intent** rather
than listing every file.

### Step 3 — Select commit type

Use Conventional Commits:

* `feat` — new task, handler, variable, template, or capability
* `fix` — bug fix or idempotency correction
* `docs` — README, role metadata documentation, inline comments
* `style` — YAML formatting, whitespace, ansible-lint cleanup
* `refactor` — restructure tasks/templates without behavior change
* `perf` — performance improvement (e.g., reduced task runs, fewer handlers)
* `test` — molecule scenarios, lint config, CI tests
* `chore` — galaxy metadata, dependencies, tooling
* `ci` — GitHub Actions, GitLab CI, pre-commit hooks

### Step 4 — Determine scope

Infer a scope from the role layout or the subsystem being changed.

Common Ansible role scopes: `tasks`, `handlers`, `templates`,
`defaults`, `vars`, `meta`, `molecule`, `docker`.

Role-specific subsystem scopes: `conf` (`tasks/conf/*`), `dovecot`
(`tasks/dovecot/*`), `tls` (`tasks/tls/*`), `debian`.

Only include a scope when it adds clarity. Prefer a subsystem scope
for feature-driven changes (e.g., `feat(tls): ...`) and a role-layout
scope for structural changes (e.g., `refactor(tasks): ...`).

### Step 5 — Write the commit message

Format exactly as:

    <type>[optional scope]: <short summary (<=50 chars)>

    <body wrapped at 72 characters>

    [optional footer(s)]

**Subject line rules:**

* Use **imperative mood** ("Add", "Fix", "Update", "Remove")
* Maximum **50 characters**
* Describe the **result**, not the implementation
* Prefer role-specific or Ansible terminology over generic phrasing

**Body rules** (required):

Explain **why the change was made**, focusing on:

* What deployment scenario or upstream behavior motivated it
* What downstream role consumers need to know to upgrade safely
* Any Ansible version constraints involved

When helpful, summarize key changes using bullet points.

**Bullet rules:**

* Use `*` (asterisk) for all bullets — never `-` or `•`
* Nested bullets indented with two spaces
* No Markdown formatting of any kind

**Ansible role expectations:**

* Call out new, renamed, or removed default variables
* Note when handler names, tag names, or public task names change
* Mention idempotency improvements when relevant
* Reference supported platforms when adding OS-specific tasks
* Flag changes to `meta/main.yml` (min Ansible version, platforms)
* Note molecule scenario additions or removals

### Breaking changes

A change is breaking when it:

* Renames or removes a default variable
* Renames or removes a handler, tag, or public task name
* Changes a default value in a way that alters runtime behavior
* Drops support for an Ansible version or OS platform
* Restructures generated configuration in a way consumers' overrides
  cannot accommodate

If the diff introduces a breaking change:

* Add `!` after the type/scope in the subject
* Include a footer: `BREAKING CHANGE: <description>`

Examples:

    feat(tasks): add preflight variable assertion block
    fix(handlers): correct service restart trigger condition
    refactor(tasks): split install and configure into files
    chore(meta): bump minimum Ansible version to 2.20
    test(molecule): add scenario for Ubuntu 24.04

    feat(defaults)!: rename primary configuration variable

    BREAKING CHANGE: old_variable_name is now new_variable_name;
    update playbook vars before upgrading.

### Step 6 — Output rules

Return **only the commit message**. Do NOT include:

* explanations or analysis
* the diff
* markdown formatting
* code fences

The output must be a clean commit message ready for `git commit`.
It will be pasted directly into a git commit editor — optimize for
copy/paste fidelity over styling.
