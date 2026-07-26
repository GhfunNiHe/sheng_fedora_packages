%global debug_package %{nil}

Name:           libssc
Version:        0.3.0
Release:        1%{?dist}
Summary:        Qualcomm Sensor Core userspace library
License:        GPLv3
URL:            https://codeberg.org/DylanVanAssche/libssc
Source0:        https://codeberg.org/DylanVanAssche/libssc/archive/main.tar.gz#/%{name}-main.tar.gz
Patch0:         wait_for_qmi_service.patch
ExclusiveArch:  aarch64
BuildRequires:  gcc meson ninja-build
BuildRequires:  glib2-devel protobuf-c-devel
BuildRequires:  libqmi-devel libmbim-devel
BuildRequires:  python3-devel
Requires:       glib2 protobuf-c libqmi

%description
Userspace library to expose Qualcomm Sensor Core (SSC) sensors via QMI.
Provides the ssccli command-line tool for interacting with SSC sensors.

%prep
%autosetup -p1 -n libssc

%build
%meson
%meson_build

%install
%meson_install

%files
%{_bindir}/ssccli
%{_libdir}/libssc.so
%{_libdir}/libssc.so.*
%{_includedir}/libssc
%{_libdir}/pkgconfig/libssc.pc
%exclude %{_libexecdir}/installed-tests
%exclude %{python3_sitelib}/ssc_server

%changelog
