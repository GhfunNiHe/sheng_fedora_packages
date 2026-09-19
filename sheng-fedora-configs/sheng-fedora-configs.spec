%global debug_package %{nil}

Name:           sheng-fedora-configs
Version:        1
Release:        2%{?dist}
Summary:        System configuration and helper scripts for Xiaomi Pad 6S Pro (sheng)
License:        Unknown
URL:            https://github.com/runesign/mipad-6s-pro-linux
BuildArch:      noarch
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  systemd-rpm-macros
Requires:       systemd
Requires:       xiaomi-sheng-firmware
Requires:       qbootctl

%global _firmwaredir %{_prefix}/lib/firmware

%description
System-wide configuration and helper scripts for the Xiaomi Pad 6S Pro (sheng).
Provides module-load, modprobe, NetworkManager, sysctl and tmpfiles drop-ins,
systemd units for boot-time setup (persist mount, WLAN MAC restoration,
bluetooth MAC fixing, audio mixer init, suspend tuning), the
auto-login/rmtfs/qbootctl/waydroid overrides, and the Android bootstrap
launcher helpers.

%prep
%autosetup

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_prefix}
cp -a usr/* %{buildroot}%{_prefix}/
# wlan_mac.bin holds the factory WLAN MAC; it lives on the read-only persist
# partition and must be visible under the firmware path when ath12k loads.
mkdir -p %{buildroot}%{_firmwaredir}/ath12k/WCN7850/hw2.0
ln -s /mnt/persist/kiwi_v2/wlan_mac.bin \
    %{buildroot}%{_firmwaredir}/ath12k/WCN7850/hw2.0/wlan_mac.bin

%files
%{_prefix}/lib/modprobe.d/sheng-wlan.conf
%{_prefix}/lib/modules-load.d/modules.conf
%{_prefix}/lib/NetworkManager/conf.d/99-sheng-wifi-mac-addr.conf
%{_prefix}/lib/sysctl.d/99-quiet-console.conf
%{_unitdir}/mnt-persist.mount
%{_unitdir}/sheng-wlan.service
%{_unitdir}/bootmac-fix-bluetooth.service
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
%{_firmwaredir}/ath12k/WCN7850/hw2.0/wlan_mac.bin

%post
%systemd_post mnt-persist.mount sheng-wlan.service bootmac-fix-bluetooth.service sheng-audio-init.service sheng-suspend-tuning.service
systemctl enable mnt-persist.mount sheng-wlan.service bootmac-fix-bluetooth.service sheng-audio-init.service sheng-suspend-tuning.service || :

%preun
%systemd_preun mnt-persist.mount sheng-wlan.service bootmac-fix-bluetooth.service sheng-audio-init.service sheng-suspend-tuning.service

%postun
%systemd_postun_with_restart sheng-wlan.service bootmac-fix-bluetooth.service sheng-audio-init.service sheng-suspend-tuning.service

%changelog
