Name:           xiaomi-sheng-firmware
Version:        1
Release:        1%{?dist}
Summary:        Firmware for Xiaomi Pad 6S Pro (sheng)
URL:            https://github.com/ianchb/sheng-firmware
Source0:        %{url}/archive/refs/heads/master.tar.gz#/%{name}-master.tar.gz
BuildArch:      noarch
License:        Unknown

%global _firmwaredir %{_prefix}/lib/firmware

%description
Firmware binaries for Xiaomi Pad 6S Pro 12.4 (sheng) with SM8550 platform.

%prep
%autosetup -n sheng-firmware-master

%install
# qcom GPU
mkdir -p %{buildroot}%{_firmwaredir}/qcom
cp -a qcom/a740_sqe.fw qcom/gmu_gen70200.bin %{buildroot}%{_firmwaredir}/qcom/

# qcom DSP
mkdir -p %{buildroot}%{_firmwaredir}/qcom/sm8550/sheng
cp -a qcom/sm8550/sheng/* %{buildroot}%{_firmwaredir}/qcom/sm8550/sheng/

# qcom topology
cp -a qcom/sm8550/Xiaomi-Pad6SPro-tplg.bin %{buildroot}%{_firmwaredir}/qcom/sm8550/

# cirrus audio
mkdir -p %{buildroot}%{_firmwaredir}/cirrus
cp -a cirrus/* %{buildroot}%{_firmwaredir}/cirrus/

# novatek touchscreen
mkdir -p %{buildroot}%{_firmwaredir}/novatek
cp -a novatek/* %{buildroot}%{_firmwaredir}/novatek/

# nanosic
mkdir -p %{buildroot}%{_firmwaredir}/nanosic
cp -a nanosic/* %{buildroot}%{_firmwaredir}/nanosic/

# ath12k WiFi
mkdir -p %{buildroot}%{_firmwaredir}/ath12k/WCN7850/hw2.0
cp -a ath12k/WCN7850/hw2.0/* %{buildroot}%{_firmwaredir}/ath12k/WCN7850/hw2.0/

# qca Bluetooth
mkdir -p %{buildroot}%{_firmwaredir}/qca
cp -a qca/* %{buildroot}%{_firmwaredir}/qca/

# fingerprint
install -Dm644 fpcsheng.elf %{buildroot}%{_firmwaredir}/fpcsheng.elf

find %{buildroot}%{_firmwaredir} -type f -exec chmod 0644 {} \;

%files
%{_firmwaredir}/qcom
%{_firmwaredir}/cirrus
%{_firmwaredir}/novatek
%{_firmwaredir}/nanosic
%{_firmwaredir}/ath12k
%{_firmwaredir}/qca
%{_firmwaredir}/fpcsheng.elf

%changelog
