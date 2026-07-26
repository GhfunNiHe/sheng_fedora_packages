%global debug_package %{nil}

Name:           alsa-xiaomi-sheng
Version:        1.0
Release:        1%{?dist}
Summary:        ALSA UCM configuration for Xiaomi Pad 6S Pro (sheng)
License:        MIT
URL:            https://github.com/map220v/alsa-ucm-conf
BuildArch:      noarch
Requires:       alsa-ucm
Source0:        %{name}-%{version}.tar.gz

%description
ALSA Use Case Manager configuration for Xiaomi Pad 6S Pro 12.4 (sheng).
Provides audio routing profiles for speakers, headphones, HDMI/DisplayPort,
and microphones via the Qualcomm SM8550 audio subsystem (WCD938X codec +
CS35L43 speaker amplifiers).

%prep
%autosetup

%build
# Nothing to build

%install
mkdir -p %{buildroot}%{_datadir}/alsa/ucm2/Xiaomi/sheng
cp -a usr/share/alsa/ucm2/Xiaomi/sheng/* %{buildroot}%{_datadir}/alsa/ucm2/Xiaomi/sheng/

%files
%defattr(644, root, root, 755)
%{_datadir}/alsa/ucm2/Xiaomi/sheng

%changelog
