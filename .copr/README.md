# Copr builds

The `copr` branch is the build branch: pushing a spec change to it rebuilds
only the affected packages on [Copr](https://copr.fedorainfracloud.org/), in
dependency order. `main` keeps using `build-sheng-rpms.yml`, which builds
everything locally with `rpmbuild`.

## How it works

`.github/workflows/copr-build.yml` selects the packages to build and then calls,
once per package:

    copr-cli buildscm <project> --clone-url <repo> --commit <sha> --type git \
        --subdir <pkg> --spec <pkg>.spec --method make_srpm

Copr's `make_srpm` method hands SRPM generation back to us, so
`.copr/make-srpm.sh` does what the CI workflow does by hand:

- download the `SourceN`/`PatchN` URLs the spec declares,
- stage the sources that live in the repository (`extra-sm8550.config`,
  `scripts/mkbootimg`, the `libssc`/`hexagonrpc` patches, the udev rules, ...),
- build the payload tarball for `alsa-xiaomi-sheng`, `sheng-sensors` and
  `sheng-fedora-configs` from their `etc/` and `usr/` trees,
- run `rpmbuild -bs` against that source directory.

Because all of it happens on the Copr side, the spec files stay unchanged:
`rpmbuild -ba` from a plain checkout keeps working exactly as before.

Builds are submitted one at a time and the workflow waits for each result,
because Copr resolves `BuildRequires` from the project's own repository, so
`fastrpc` and `libssc` have to exist before `iio-sensor-proxy`,
`xiaomi-sheng-thp`, `xiaomi-sheng-keyboard-helper` and `hexagonrpc` are built.
`kernel-sm8550` runs in a separate job: nothing depends on it, it needs network
access during `%prep` (`git ls-remote`), and it takes hours.

## One-time setup

1. Create the Copr project (default name `sheng_fedora_packages`, override with
   the repository variable `COPR_PROJECT`):

       copr-cli create sheng_fedora_packages --chroot fedora-44-aarch64 \
           --chroot fedora-44-x86_64 \
           --description "Fedora packages for the Xiaomi Pad 6S Pro (sheng)"

   Every compiled package is `ExclusiveArch: aarch64`, so an aarch64 chroot is
   required; the noarch ones build in either.

2. Raise the build timeout in the project settings. Copr's default is 5 hours;
   the kernel is submitted with `--timeout 21600` (6 hours).

3. Create an API token at <https://copr.fedorainfracloud.org/api/> and store it
   as repository secrets:

   | Secret | Value |
   | --- | --- |
   | `COPR_LOGIN` | API login |
   | `COPR_USERNAME` | Copr username |
   | `COPR_TOKEN` | API token |
   | `COPR_API_URL` | optional, defaults to `https://copr.fedorainfracloud.org` |

4. Create the branch and push it:

       git checkout -b copr
       git push -u origin copr

   The first push builds every package, later pushes build only what changed.
   `workflow_dispatch` accepts an optional space-separated list of package
   directories; empty means "everything".

## Notes

- `sheng-sensors` ships Qualcomm sensor configuration blobs and
  `xiaomi-sheng-firmware` ships vendor firmware, both with redistribution terms
  that Copr's terms of service do not allow. To keep them off Copr, set the
  repository variable `SKIP_PACKAGES` to
  `sheng-sensors xiaomi-sheng-firmware`; they stay in the GitHub releases.
- There is no ccache on Copr, so expect a cold, slow first kernel build.
- `COPR_STUB_SOURCES=1 .copr/make-srpm.sh <spec> <outdir>` stages placeholder
  files instead of downloading, which is handy for checking the packaging logic
  without pulling a kernel tarball.
