# Legacy OS guard for trixie-next (proposed)

Only Debian `bullseye` and `bookworm` trigger this guard. Trixie and future
codenames are not redirected. An unreadable OS identity aborts rather than
guessing. This is not a replacement for other OS/runtime compatibility checks.

`runs/update_self.sh` redirects a `trixie-next` request before checkout to the
latest stable 2.0–2.4 release tag, including `-Patch.N` releases. Beta/RC tags,
2.5 and future major releases are excluded even if they become the latest
regular Release. This compatibility ceiling follows the requirement that 2.5
needs the system update; it must be reviewed if the release policy changes.
The current upstream stable tag observed during preparation was `2.3.0`.

Old installed updaters do not contain this new check. They may already have
checked out trixie-next before its new `atreboot.sh` runs. Its very early guard
then invokes the guarded updater and exits the incompatible startup path before
virtualenv, package, boot configuration, service or network migrations.
Preventing that original checkout also requires a backport into a regular
release, and cannot retroactively change already installed old updaters.

The updater fetches refs, validates the selected tag, and uses the existing
Release checkout/metadata/reboot path. Missing compatible tags, fetch failures
or failed checkout abort without reboot or a false success announcement. The
fixed German warning is published through the system Python/local MQTT broker
after successful checkout, before the existing reboot. MQTT errors are bounded
and do not block recovery. Publication does not guarantee that the user saw it;
this patch does not add a persistent notification outbox.

No configuration, target backup, broker database or application data restore is
performed by the guard. Existing updater operations are otherwise unchanged.
There is no automatic OS update.

## Verification

- `python3 -m unittest discover -s tests`: 47 tests passed on Linux, including
  ten new sandboxed guard tests.
- New guard tests also passed on macOS. The complete suite requires Linux's
  `flock`; unrelated native-display tests fail without it on macOS.
- Shell syntax and `git diff --check` passed.
- No real device checkout, reboot, package operation or migration was performed.
- A full legacy-device recovery test, notification visibility across reboot,
  and failure recovery on hardware remain unqualified.

Branch: `fix/legacy-os-trixie-fallback`, based on `openWB/core`'s `trixie-next`
at `4bf1d2cde46675755e282fe78a5e65ac3b051793`.
Fork: https://github.com/kevinwieland/core . Publication of this branch was
approved; a PR targeting `openWB/core:trixie-next` awaits separate approval.
