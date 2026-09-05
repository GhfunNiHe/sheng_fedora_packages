%global debug_package %{nil}

Name:           sheng-fedora-configs
Version:        1
Release:        1%{?dist}
Summary:        System configuration and helper scripts for Xiaomi Pad 6S Pro (sheng)
License:        Unknown
URL:            https://github.com/runesign/mipad-6s-pro-linux
BuildArch:      noarch
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  systemd-rpm-macros
Requires:       systemd

%description
System-wide configuration and helper scripts for the Xiaomi Pad 6S Pro (sheng).
Provides module-load, modprobe, NetworkManager, sysctl and tmpfiles drop-ins,
systemd units for boot-time setup (MAC fixing, audio mixer init, suspend
tuning), the auto-login/rmtfs/qbootctl/waydroid overrides, and the Android
bootstrap launcher helpers.

%prep
%autosetup

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_prefix}
cp -a usr/* %{buildroot}%{_prefix}/

%files
%{_prefix}/lib/modprobe.d/cfg80211.conf
%{_prefix}/lib/modules-load.d/modules.conf
%{_prefix}/lib/NetworkManager/conf.d/22-wifi-mac-addr.conf
%{_prefix}/lib/sysctl.d/99-quiet-console.conf
%{_unitdir}/bootmac-fix-bluetooth.service
%{_unitdir}/bootmac-fix-wlan.service
%{_unitdir}/sheng-audio-init.service
%{_unitdir}/sheng-suspend-tuning.service
%{_unitdir}/getty@tty1.service.d/autologin.conf
%{_unitdir}/qbootctl.service.d/10-udev-settle.conf
%{_unitdir}/rmtfs.service.d/10-sheng-no-rproc-sync.conf
%{_unitdir}/waydroid-container.service.d/99-clean-stop.conf
%{_prefix}/lib/tmpfiles.d/99-sheng-x11-unix.conf
%{_prefix}/lib/systemd/system-shutdown/f2fs-root-shutdown
%{_bindir}/sta
%{_libexecdir}/bootmac-fix
%{_libexecdir}/sheng-audio-init
%{_libexecdir}/sheng-suspend-tuning
%{_datadir}/applications/Android.desktop
%{_datadir}/icons/hicolor/scalable/apps/android.svg

%post
%systemd_post bootmac-fix-bluetooth.service bootmac-fix-wlan.service sheng-audio-init.service sheng-suspend-tuning.service
systemctl enable bootmac-fix-bluetooth.service bootmac-fix-wlan.service sheng-audio-init.service sheng-suspend-tuning.service || :

%preun
%systemd_preun bootmac-fix-bluetooth.service bootmac-fix-wlan.service sheng-audio-init.service sheng-suspend-tuning.service

%postun
%systemd_postun_with_restart bootmac-fix-bluetooth.service bootmac-fix-wlan.service sheng-audio-init.service sheng-suspend-tuning.service

%changelog
