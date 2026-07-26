%global debug_package %{nil}

Name:           xiaomi-mipps-auth
Version:        0.21
Release:        1%{?dist}
Summary:        Xiaomi MiPPS charger authentication for sheng
License:        GPL-2.0-only
URL:            https://github.com/ianchb/xiaomi-mipps-auth
Source0:        %{url}/archive/refs/heads/master.tar.gz#/%{name}-master.tar.gz
BuildArch:      noarch
BuildRequires:  systemd-rpm-macros
Requires:       python3 util-linux

%description
Automatic Xiaomi MiPPS charger authentication daemon for Xiaomi Pad 6S Pro.
Handles PD/VDM handshake with Xiaomi chargers to enable fast charging and
sends desktop notifications about charge status.

%prep
%autosetup -n %{name}-master

%build
# Python script, no compilation

%install
install -Dm755 xiaomi-mipps-auth %{buildroot}%{_libexecdir}/xiaomi-mipps-auth
install -Dm644 xiaomi-mipps-auth.service %{buildroot}%{_unitdir}/xiaomi-mipps-auth.service
install -Dm644 90-xiaomi-mipps-auth.rules %{buildroot}%{_udevrulesdir}/90-xiaomi-mipps-auth.rules

%files
%attr(755, root, root) %{_libexecdir}/xiaomi-mipps-auth
%{_unitdir}/xiaomi-mipps-auth.service
%{_udevrulesdir}/90-xiaomi-mipps-auth.rules

%post
%systemd_post xiaomi-mipps-auth.service
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload || :
fi

%changelog
