#!/usr/bin/env bash
#
# SRPM generation for Copr's "make srpm" SCM build method.
#
# Copr invokes this as root inside a mock chroot of the builder host's Fedora
# release, with the network available and with the working directory set to the
# package's Subdirectory:
#
#     make -f <cloned repo>/.copr/Makefile srpm outdir=<dir> spec=<spec>
#
# Collecting the sources here, instead of pointing the spec files at download
# URLs, keeps every spec buildable with a plain `rpmbuild -ba` straight from a
# checkout -- which is what build-sheng-rpms.yml and day-to-day work rely on.
set -euo pipefail

spec_arg="${1:?usage: make-srpm.sh <spec> <outdir>}"
outdir_arg="${2:?usage: make-srpm.sh <spec> <outdir>}"

# Fedora's libfprint source is needed by xiaomi-sheng-fingerprint but is not
# kept in git; pinned to the same version build-sheng-rpms.yml falls back to.
libfprint_url="${LIBFPRINT_URL:-https://gitlab.freedesktop.org/libfprint/libfprint/-/archive/v1.94.10/libfprint-v1.94.10.tar.gz}"

log() { printf '==> %s\n' "$*"; }

# --------------------------------------------------------------- locations
if [ -f "$spec_arg" ]; then
    spec="$(cd "$(dirname "$spec_arg")" && pwd)/$(basename "$spec_arg")"
else
    spec="$(find "$PWD" -maxdepth 3 -name "$(basename "$spec_arg")" -print -quit)"
fi
if [ -z "${spec:-}" ] || [ ! -f "$spec" ]; then
    echo "make-srpm: spec file not found: $spec_arg (cwd: $PWD)" >&2
    exit 1
fi

pkgdir="$(dirname "$spec")"
pkg="$(basename "$pkgdir")"
repodir="$(dirname "$pkgdir")"

log "package $pkg"

# ----------------------------------------------------------------- tooling
missing=()
for tool in rpmbuild spectool curl tar gzip xz bzip2; do
    command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [ ${#missing[@]} -gt 0 ]; then
    log "installing SRPM tooling (missing: ${missing[*]})"
    dnf -y install rpm-build rpmdevtools tar gzip xz bzip2 curl findutils
fi

# -------------------------------------------------------------- source dir
srcdir="$(mktemp -d)"
workdir="$(mktemp -d)"
trap 'rm -rf "$srcdir" "$workdir"' EXIT

stub="${COPR_STUB_SOURCES:-0}"
if [ "$stub" = "1" ]; then
    log "COPR_STUB_SOURCES=1: URL sources get empty placeholders (local smoke test only)"
fi

fetch() {  # fetch <url> <filename>
    local url="$1" name="$2"
    if [ "$stub" = "1" ]; then
        : > "$srcdir/$name"
        return
    fi
    log "fetching $name"
    curl -fL --retry 3 --retry-delay 2 --connect-timeout 30 -o "$srcdir/$name" "$url"
}

# Every SourceN/PatchN the spec declares, with %-macros expanded by spectool.
# URL entries may carry a "#/name" fragment pinning the file name; the rest are
# files that live next to the spec (or, like scripts/*, in the repo root).
stage_declared_sources() {
    local tag value url name candidate
    while read -r tag value; do
        [ -n "$value" ] || continue
        if [[ "$value" == *"://"* ]]; then
            url="${value%%#*}"
            if [[ "$value" == *"#/"* ]]; then
                name="${value##*#/}"
            else
                name="$(basename "${url%%\?*}")"
            fi
            fetch "$url" "$name"
            continue
        fi
        name="$(basename "$value")"
        for candidate in "$pkgdir/$name" "$pkgdir/$value" "$repodir/$value"; do
            [ -f "$candidate" ] || continue
            log "staging local source $name"
            cp -a "$candidate" "$srcdir/$name"
            break
        done
    done < <(spectool -l "$spec" 2>/dev/null |
             sed -n 's/^\(Source[0-9]*\|Patch[0-9]*\):[[:space:]]*\([^[:space:]]*\)[[:space:]]*$/\1 \2/p')
}
stage_declared_sources

# ------------------------------------------------------- package specifics
case "$pkg" in
    alsa-xiaomi-sheng|sheng-sensors|sheng-fedora-configs)
        # Payload-only packages: Source0 is a tarball of this repository's own
        # etc/usr trees, so it is generated here rather than stored in git.
        name="$(rpmspec -q --qf '%{NAME}-%{VERSION}' "$spec")"
        log "building payload tarball $name.tar.gz"
        mkdir -p "$workdir/$name"
        for tree in etc usr; do
            [ -d "$pkgdir/$tree" ] && cp -a "$pkgdir/$tree" "$workdir/$name/"
        done
        tar -czf "$srcdir/$name.tar.gz" -C "$workdir" "$name"
        rm -rf "$workdir/$name"
        ;;
    kernel-sm8550)
        # Source2 is scripts/mkbootimg, which sits at the repository root
        # instead of next to the spec.
        kb="$(find "$repodir" -maxdepth 3 -type f -name mkbootimg -print -quit)"
        if [ -z "$kb" ]; then
            echo "make-srpm: scripts/mkbootimg not found under $repodir" >&2
            exit 1
        fi
        log "staging mkbootimg from $kb"
        install -m755 "$kb" "$srcdir/mkbootimg"
        ;;
    xiaomi-sheng-fingerprint)
        # Source1: the libfprint source archive the private build patches.
        fetch "$libfprint_url" libfprint-src.tar.xz
        ;;
esac

# ---------------------------------------------------------------- rpmbuild
mkdir -p "$outdir_arg"
outdir="$(cd "$outdir_arg" && pwd)"
topdir="$workdir/topdir"
mkdir -p "$topdir"/BUILD "$topdir"/BUILDROOT "$topdir"/RPMS "$topdir"/SOURCES "$topdir"/SPECS "$topdir"/SRPMS
mkdir -p "$workdir/tmp"

log "sources staged in $srcdir"
ls -A "$srcdir" | sed 's/^/    /'

log "generating SRPM"
rpmbuild -bs "$spec" \
    --define "_topdir $topdir" \
    --define "_sourcedir $srcdir" \
    --define "_specdir $pkgdir" \
    --define "_builddir $topdir/BUILD" \
    --define "_rpmdir $topdir/RPMS" \
    --define "_buildrootdir $topdir/BUILDROOT" \
    --define "_tmppath $workdir/tmp" \
    --define "_srcrpmdir $outdir"

log "SRPM written to"
ls -l "$outdir"/*.src.rpm | sed 's/^/    /'
