%global debug_package %{nil}

Name:           sheng-sensors
Version:        20240917
Release:        1%{?dist}
Summary:        Sensor configuration files for Xiaomi Pad 6S Pro (sheng)
License:        Proprietary
URL:            https://github.com/ianchb/sm8550-mainline
BuildArch:      noarch
Requires:       iio-sensor-proxy-sheng
Source0:        %{name}-%{version}.tar.gz

%description
Proprietary sensor configuration files (JSON configs, udev rules, systemd
overrides) for the Qualcomm Sensor Core on Xiaomi Pad 6S Pro (SM8550).

%prep
%autosetup

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_prefix}
cp -a usr/* %{buildroot}%{_prefix}/

%files
%dir %{_datadir}/qcom
%{_datadir}/qcom/conf.d
%{_datadir}/qcom/sm8550
%{_prefix}/lib/udev/rules.d/81-sheng-ssc-sensors.rules
%{_prefix}/lib/udev/rules.d/99-touchscreen-sheng.rules
%{_prefix}/lib/systemd/system/iio-sensor-proxy.service.d/10-sheng-sensors.conf

%post
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload || :
    if [ -e /sys/devices/virtual/misc/fastrpc-adsp ]; then
        udevadm trigger /sys/devices/virtual/misc/fastrpc-adsp || :
    fi
fi
if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || :
    if [ -d /run/systemd/system ]; then
        systemctl try-restart iio-sensor-proxy.service || :
    fi
fi

%changelog
