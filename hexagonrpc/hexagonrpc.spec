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
Release:        2%{?dist}
Summary:        Modern userspace library and reverse-RPC daemon for Qualcomm FastRPC
License:        GPL-3.0-or-later
URL:            https://github.com/lzxcr/hexagonrpc
Source0:        %{url}/archive/%{commit}.tar.gz#/%{name}-%{commit}.tar.gz
# Patches and sheng-specific data files pulled from lzxcr/arch-xiaomi-sheng
# commit 7ba7526892c03fc815f293230ea1c965328565b1 (files/install/hexagonrpc/).
# They were written against the pinned %%commit and apply with -p1.
Patch0:         config-malformed.patch
Patch1:         invoke-result.patch
Patch2:         android-rfsa.patch
Source1:        60-hexagonrpc.rules
Source2:        hexagonrpc-sheng.json
ExclusiveArch:  aarch64

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  cargo >= 1.85
BuildRequires:  rust >= 1.85
Requires:       glibc
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
cd %{name}-v%{version}
# Same order and prefixes as the upstream Arch PKGBUILD (prepare()).
%patch -P0 -p1
%patch -P1 -p1
%patch -P2 -p1

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
install -Dm0755 target/release/hexagonrpc-probe %{buildroot}%{_bindir}/hexagonrpc-probe
install -Dm0755 target/release/sns-registrygen %{buildroot}%{_bindir}/sns-registrygen
make -C data DESTDIR=%{buildroot} PREFIX=/usr install

# Device discovery grants access only. Static PD listeners are optional
# consumers and must never be pulled into boot or the kernel audio path.
# Overrides the rule installed by data/Makefile (same file name).
install -Dm0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/60-hexagonrpc.rules

# The stock Qualcomm sensor config writes its registry below
# /mnt/vendor/persist, while upstream only mapped the /persist alias at the
# pinned commit. A per-device config takes precedence over the global one.
install -Dm0644 %{SOURCE2} %{buildroot}%{_datadir}/qcom/sm8550/Xiaomi/sheng/hexagonrpc.json

# Bound recovery attempts so future firmware faults cannot turn remoteproc
# recovery plus udev auto-start into an unlimited crash loop.
for unit in %{buildroot}%{_unitdir}/hexagonrpcd-*.service; do
  sed -i '/^ConditionPathExists=/a StartLimitBurst=3' "${unit}"
  sed -i '/^ConditionPathExists=/a StartLimitIntervalSec=60s' "${unit}"
done

# Docs/license are installed explicitly instead of via %doc/%license, which
# resolve against the top-level build subdir rather than our nested source dir.
install -Dm0644 COPYING %{buildroot}%{_licensedir}/%{name}/COPYING
install -d %{buildroot}%{_docdir}/%{name}
install -m0644 README.md docs/*.md %{buildroot}%{_docdir}/%{name}/

%files
%{_bindir}/hexagonrpcd
%{_bindir}/hexagonrpc-probe
%{_bindir}/sns-registrygen
%dir %{_datadir}/qcom
%dir %{_datadir}/qcom/conf.d
%{_datadir}/qcom/conf.d/hexagonrpc.json
%dir %{_datadir}/qcom/sm8550
%dir %{_datadir}/qcom/sm8550/Xiaomi
%dir %{_datadir}/qcom/sm8550/Xiaomi/sheng
%{_datadir}/qcom/sm8550/Xiaomi/sheng/hexagonrpc.json
%{_unitdir}/hexagonrpcd-*.service
%{_udevrulesdir}/60-hexagonrpc.rules
%{_sysusersdir}/hexagonrpc.conf
%{_mandir}/man3/hexagonrpc.3*
%{_mandir}/man8/hexagonrpcd.8*
%{_mandir}/man8/hexagonrpcd-*.8*
%{_mandir}/man8/hexagonrpc-probe.8*
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
* Sat Sep 19 2026 Sheng Fedora packagers - 0.6.0-2
- Sync with arch-xiaomi-sheng commit 7ba7526: add config-malformed,
  invoke-result and android-rfsa patches; ship hexagonrpc-probe and its man
  page; replace the udev rule with a permission-only variant (no udev
  auto-start of listeners); ship a per-device sheng HexagonFS path config;
  bound listener service restarts (StartLimitIntervalSec/StartLimitBurst).
* Sat Sep 05 2026 HexagonRPC contributors - 0.6.0-1
- Initial RPM packaging of HexagonRPC 0.6.0, derived from the Arch PKGBUILD.
