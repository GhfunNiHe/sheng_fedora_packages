# hexagonrpc RPM spec — derived from the upstream Arch PKGBUILD.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Packaging notes:
#   * Upstream is released from the git tag v0.6.0; create that tag
#     before producing a source release (see README "### Arch Linux 安装").
#   * Until the v0.6.0 tag is pushed, we pin Source0 to the Rust-rewrite
#     commit db659bd (the current HEAD). Switch back to
#     %{url}/archive/refs/tags/v%{version}.tar.gz once the tag exists.
#   * data/Makefile installs systemd units, udev rules, sysusers, man pages
#     and the default path-mapping config under PREFIX=/usr.
#   * Cargo.lock is committed, so we build with --locked (network is needed
#     to fetch crates.io dependencies; --frozen would require a prefilled
#     cargo cache).

%global debug_package %{nil}
%global commit db659bd

Name:           hexagonrpc
Version:        0.6.0
Release:        1%{?dist}
Summary:        Modern userspace library and reverse-RPC daemon for Qualcomm FastRPC
License:        GPL-3.0-or-later
URL:            https://github.com/lzxcr/hexagonrpc
Source0:        %{url}/archive/%{commit}.tar.gz#/%{name}-%{commit}.tar.gz
ExclusiveArch:  aarch64

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  cargo >= 1.85
BuildRequires:  rust >= 1.85
Requires:       glibc
Requires:       libgcc
Requires:       systemd
Requires(post):    systemd
Requires(postun):  systemd

# The upstream FastRPC/libfastrpc/dsprpcd expose the same DSP-facing interfaces
# (apps_std/apps_mem/remotectl/adsp_listener) and drive the same /dev/fastrpc-*
# nodes. This clean-room implementation is wire- and interface-compatible but
# NOT binary-compatible (hexagonrpcd / Rust rlib, not dsprpcd / libfastrpc.so),
# so it must not be installed alongside those packages.
Conflicts:      dsprpcd
Conflicts:      fastrpc
# If this also ships a libfastrpc replacement .so, uncomment:
# Conflicts:    libfastrpc
# If this supersedes a distro-packaged daemon/lib, add a curated Obsoletes, e.g.:
# Obsoletes:    fastrpc < 0.6.0

%description
Modern userspace library and reverse-RPC daemon for Qualcomm FastRPC. It
provides the fastrpc/fastrpc2 ioctl wrapper, rpcmem, a reverse-tunnel daemon
serving the apps_std/apps_mem/remotectl interfaces, and a HexagonFS virtual
filesystem that redirects Android firmware paths to local Linux files.

%prep
# GitHub tag tarballs extract to hexagonrpc-v0.6.0; use a plain tar here so
# the build is independent of how the source file is named in SOURCES.
rm -rf %{name}-v%{version}
mkdir %{name}-v%{version}
tar -xzf %{SOURCE0} --strip-components=1 -C %{name}-v%{version}

%build
cd %{name}-v%{version}
export CARGO_TARGET_DIR=target
cargo build --locked --release --workspace

%check
cd %{name}-v%{version}
export CARGO_TARGET_DIR=target
cargo test --locked --workspace

%install
cd %{name}-v%{version}
install -Dm0755 target/release/hexagonrpcd %{buildroot}%{_bindir}/hexagonrpcd
install -Dm0755 target/release/sns-registrygen %{buildroot}%{_bindir}/sns-registrygen
make -C data DESTDIR=%{buildroot} PREFIX=/usr install
# Docs/license are installed explicitly instead of via %doc/%license, which
# resolve against the top-level build subdir rather than our nested source dir.
install -Dm0644 COPYING %{buildroot}%{_licensedir}/%{name}/COPYING
install -d %{buildroot}%{_docdir}/%{name}
install -m0644 README.md docs/*.md %{buildroot}%{_docdir}/%{name}/

%files
%{_bindir}/hexagonrpcd
%{_bindir}/sns-registrygen
%dir %{_datadir}/qcom
%dir %{_datadir}/qcom/conf.d
%{_datadir}/qcom/conf.d/hexagonrpc.json
%{_unitdir}/hexagonrpcd-*.service
%{_udevrulesdir}/60-hexagonrpc.rules
%{_sysusersdir}/hexagonrpc.conf
%{_mandir}/man3/hexagonrpc.3*
%{_mandir}/man8/hexagonrpcd.8*
%{_mandir}/man8/hexagonrpcd-*.8*
%{_licensedir}/%{name}/COPYING
%{_docdir}/%{name}/README.md
%{_docdir}/%{name}/QUICKSTART.md
%{_docdir}/%{name}/ARCHITECTURE.md
%{_docdir}/%{name}/API.md
%{_docdir}/%{name}/CONFIGURATION.md

%post
# Create the hexagonrpc user/group used by the unit files and udev rules.
systemd-sysusers || :
systemctl daemon-reload || :

%postun
systemctl daemon-reload || :

%changelog
* Sat Sep 05 2026 HexagonRPC contributors - 0.6.0-1
- Initial RPM packaging of HexagonRPC 0.6.0, derived from the Arch PKGBUILD.
