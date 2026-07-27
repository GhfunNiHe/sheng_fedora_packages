%global debug_package %{nil}

Name:           iio-sensor-proxy-sheng
Version:        3.9
Release:        1%{?dist}
Provides:       iio-sensor-proxy = %{version}-%{release}
Conflicts:      iio-sensor-proxy
Summary:        IIO sensors to D-Bus proxy (with Qualcomm SSC support)
License:        GPLv3
URL:            https://gitlab.freedesktop.org/hadess/iio-sensor-proxy
Source0:        %{url}/-/archive/%{version}/iio-sensor-proxy-%{version}.tar.gz
ExclusiveArch:  aarch64
BuildRequires:  gcc meson ninja-build
BuildRequires:  glib2-devel libgudev-devel polkit-devel
BuildRequires:  pkgconfig(udev) dbus-devel
BuildRequires:  libssc libqmi-devel libmbim-devel
BuildRequires:  systemd-rpm-macros
Requires:       dbus glib2 libgudev polkit
Requires:       libssc systemd

%description
iio-sensor-proxy with Qualcomm Sensor Core (SSC) support enabled.
Proxies IIO sensor data to D-Bus, enabling accelerometer, ambient light,
and proximity sensor access on Xiaomi Pad 6S Pro (SM8550).

%prep
%autosetup -n iio-sensor-proxy-%{version}

%build
%meson \
    -Db_lto=true \
    -Dssc-support=enabled \
    -Dsystemdsystemunitdir=%{_unitdir}
%meson_build

%install
%meson_install

%files
%{_bindir}/monitor-sensor
%{_libexecdir}/iio-sensor-proxy
%{_unitdir}/iio-sensor-proxy.service
%{_udevrulesdir}/80-iio-sensor-proxy.rules
%{_datadir}/dbus-1/system.d/net.hadess.SensorProxy.conf
%{_datadir}/polkit-1/actions/net.hadess.SensorProxy.policy

%post
%systemd_post iio-sensor-proxy.service

%preun
%systemd_preun iio-sensor-proxy.service

%postun
%systemd_postun_with_restart iio-sensor-proxy.service

%changelog
