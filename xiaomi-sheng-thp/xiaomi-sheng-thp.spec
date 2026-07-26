%global debug_package %{nil}

Name:           xiaomi-sheng-thp
Version:        0.3.9
Release:        1%{?dist}
Summary:        Touch Host Processor for Xiaomi Pad 6S Pro
License:        Apache-2.0
URL:            https://github.com/ianchb/xiaomi-sheng-thp
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-v%{version}.tar.gz
ExclusiveArch:  aarch64
BuildRequires:  gcc-c++ glib2-devel libssc bluez-libs-devel
BuildRequires:  systemd-rpm-macros
Requires:       libssc glib2

%description
Touch Host Processor for Xiaomi Pad 6S Pro 12.4 (sheng). Reads raw THP frames
from the kernel and creates standard Linux input devices through uinput for
the Novatek NT36532E touch controller.

%prep
%autosetup -n %{name}-%{version}

%build
# Add /usr/include/glib-2.0 and /usr/lib64/glib-2.0 to pkg-config path if needed
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig:%{_datadir}/pkgconfig
make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot} PREFIX=%{_prefix} LIBEXECDIR=%{_libexecdir}/xiaomi-sheng-thp

%files
%{_libexecdir}/xiaomi-sheng-thp/xiaomi-sheng-thp
%{_unitdir}/xiaomi-sheng-thp.service
%doc %{_docdir}/xiaomi-sheng-thp

%post
%systemd_post xiaomi-sheng-thp.service

%preun
%systemd_preun xiaomi-sheng-thp.service

%postun
%systemd_postun_with_restart xiaomi-sheng-thp.service

%changelog
