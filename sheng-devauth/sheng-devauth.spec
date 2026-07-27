%global debug_package %{nil}

Name:           sheng-devauth
Version:        1.0
Release:        1%{?dist}
Summary:        Xiaomi Keyboard authentication daemon for sheng
License:        GPLv3
URL:            https://github.com/ianchb/sheng_devauth
Source0:        %{url}/archive/refs/heads/main.tar.gz#/%{name}-main.tar.gz
ExclusiveArch:  aarch64
BuildRequires:  gcc make systemd-rpm-macros

%description
Service used in pair with kernel driver to authenticate Xiaomi Keyboard
on Xiaomi Pad 6S Pro (sheng).

%prep
%autosetup -n sheng_devauth-main

%build
make %{?_smp_mflags}

%install
install -Dm755 xiaomi_devauth %{buildroot}%{_bindir}/xiaomi_devauth

# systemd service
# systemd service
mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/sheng-devauth.service << 'EOF'
[Unit]
Description=Xiaomi DevAuth Service

[Service]
Type=simple
ExecStart=%{_bindir}/xiaomi_devauth
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=sysinit.target
EOF

install -d %{buildroot}%{_unitdir}/sheng-devauth.service.d
cat > %{buildroot}%{_unitdir}/sheng-devauth.service.d/qtee.conf << 'EOF'
[Unit]
Requires=qteesupplicant.service
After=qteesupplicant.service
EOF

%files
%attr(755, root, root) %{_bindir}/xiaomi_devauth
%{_unitdir}/sheng-devauth.service
%dir %{_unitdir}/sheng-devauth.service.d
%config(noreplace) %{_unitdir}/sheng-devauth.service.d/qtee.conf

%post
%systemd_post sheng-devauth.service
systemctl enable sheng-devauth.service

%preun
%systemd_preun sheng-devauth.service

%postun
%systemd_postun_with_restart sheng-devauth.service

%changelog
