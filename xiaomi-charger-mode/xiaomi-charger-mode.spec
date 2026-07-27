%global debug_package %{nil}

Name:           xiaomi-charger-mode
Version:        0.20
Release:        1%{?dist}
Summary:        Charger mode boot handler for Xiaomi Pad 6S Pro
License:        GPL-2.0-only
URL:            https://github.com/ianchb/xiaomi-charger-mode
Source0:        %{url}/archive/refs/tags/%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  systemd-rpm-macros
Requires:       python3

%description
When the kernel command line contains androidboot.mode=charger, this service
blocks normal boot, draws a framebuffer charging screen, runs xiaomi-mipps-auth
for fast charging, and handles power-off when unplugged or reboot on long-press.

%prep
%autosetup -n %{name}-%{version}

%build
# Python script, no compilation

%install
install -Dm755 xiaomi-charger-mode %{buildroot}%{_libexecdir}/xiaomi-charger-mode
install -Dm644 xiaomi-charger-mode.service %{buildroot}%{_unitdir}/xiaomi-charger-mode.service

%files
%attr(755, root, root) %{_libexecdir}/xiaomi-charger-mode
%{_unitdir}/xiaomi-charger-mode.service

%post
%systemd_post xiaomi-charger-mode.service
systemctl enable xiaomi-charger-mode.service

%preun
%systemd_preun xiaomi-charger-mode.service

%postun
%systemd_postun_with_restart xiaomi-charger-mode.service

%changelog
