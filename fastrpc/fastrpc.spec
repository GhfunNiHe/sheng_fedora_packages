%global debug_package %{nil}
%global fastrpc_ver 1.0.2

Name:           fastrpc
Version:        %{fastrpc_ver}
Release:        1%{?dist}
Summary:        Qualcomm FastRPC userspace library
License:        BSD
URL:            https://github.com/qualcomm/fastrpc
Source0:        %{url}/archive/refs/tags/v%{version}.zip
ExclusiveArch:  aarch64
BuildRequires:  gcc gcc-c++ make autoconf automake libtool
BuildRequires:  libyaml-devel
BuildRequires:  systemd-rpm-macros
Requires:       libyaml
Requires:       systemd

%description
FastRPC implementation for Qualcomm DSP communication. Provides the adsprpcd
daemon for communicating with the aDSP (Audio/Sensor DSP) on SM8550 platforms.

%prep
%autosetup -n fastrpc-%{version}

%build
autoreconf -is
%configure
%make_build

%install
%make_install

# systemd service for sensorspd
mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/adsprpcd-sensorspd.service << 'EOF'
[Unit]
Description=sensorspd aDSP RPC daemon
ConditionPathExists=|/dev/fastrpc-adsp
ConditionPathExists=|/dev/fastrpc-adsp-secure
Before=iio-sensor-proxy.service

[Service]
Type=exec
ExecStart=%{_bindir}/adsprpcd sensorspd
Restart=on-failure
RestartSec=5

[Install]
WantedBy=iio-sensor-proxy.service
EOF

%files
%{_bindir}/adsprpcd
%{_bindir}/cdsprpcd
%{_bindir}/gdsprpcd
%{_bindir}/sdsprpcd
%{_libdir}/*.so
%{_libdir}/*.so.*
%exclude %{_bindir}/fastrpc_test
%exclude %{_includedir}/fastrpc
%exclude %{_libdir}/fastrpc_test
%exclude %{_datadir}/fastrpc_test
%{_unitdir}/adsprpcd-sensorspd.service

%post
%systemd_post adsprpcd-sensorspd.service

%preun
%systemd_preun adsprpcd-sensorspd.service

%postun
%systemd_postun_with_restart adsprpcd-sensorspd.service

%changelog
