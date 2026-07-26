%global debug_package %{nil}

Name:           xiaomi-pen-status
Version:        0.2.3
Release:        1%{?dist}
Summary:        Stylus pen status tray utility for Xiaomi Pad 6S Pro
License:        GPL-2.0-only
URL:            https://github.com/ianchb/xiaomi-pen-status
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-v%{version}.tar.gz
ExclusiveArch:  aarch64
BuildRequires:  qt6-qtbase-devel qt6-qtsvg-devel
Requires:       qt6-qtbase qt6-qtsvg

%description
Small Qt tray utility that displays stylus power-state attributes exported
by qcom_battmgr for the Xiaomi Pad 6S Pro 12.4 (sheng).

%prep
%autosetup -n %{name}-%{version}

%build
qmake6 xiaomi-pen-status.pro
make %{?_smp_mflags}

%install
install -Dm755 xiaomi-pen-status %{buildroot}%{_bindir}/xiaomi-pen-status
install -Dm644 xiaomi-pen-status.desktop %{buildroot}%{_datadir}/applications/xiaomi-pen-status.desktop
install -Dm644 xiaomi-pen-status.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/xiaomi-pen-status.svg

%files
%{_bindir}/xiaomi-pen-status
%{_datadir}/applications/xiaomi-pen-status.desktop
%{_datadir}/icons/hicolor/scalable/apps/xiaomi-pen-status.svg

%changelog
