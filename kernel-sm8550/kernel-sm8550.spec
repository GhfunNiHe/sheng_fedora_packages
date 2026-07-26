%undefine        _debugsource_packages
%global KERNEL_VER 7.1.5
%global KERNEL_CUSTOM_VER 1
%global RELEASE_VER 4
%global DEVICE_NAME sheng
%global PLATFORM_NAME sm8550

%global KERNEL_EXTRA_VER -%{PLATFORM_NAME}-%{KERNEL_CUSTOM_VER}-%{RELEASE_VER}
%global KERNEL_FULL_VER %{KERNEL_VER}%{KERNEL_EXTRA_VER}


Version:         %{KERNEL_VER}.%{PLATFORM_NAME}.%{KERNEL_CUSTOM_VER}
Release:         %{RELEASE_VER}.%{DEVICE_NAME}%{?dist}
ExclusiveArch:  aarch64
Name:            kernel-%{PLATFORM_NAME}
Summary:         Mainline Linux kernel for %{PLATFORM_NAME} devices
License:         GPLv2
URL:             https://github.com/ianchb/sm8550-mainline
Source0:         %{url}/archive/sheng-%{KERNEL_VER}.tar.gz
Source1:         https://github.com/ianchb/sm8550-mainline/releases/download/%{KERNEL_VER}/sm8550.config
Source2:         scripts/mkbootimg

BuildRequires:   bc bison dwarves diffutils elfutils-devel findutils git-core hmaccalc hostname make openssl-devel perl-interpreter rsync tar which flex bzip2 xz zstd python3 python3-devel python3-pyyaml rust rust-src bindgen rustfmt clippy opencsd-devel net-tools
BuildRequires:   clang lld llvm ccache systemd-boot systemd-ukify

Provides:        kernel               = %{version}-%{release}
Provides:        kernel-core          = %{version}-%{release}
Provides:        kernel-modules       = %{version}-%{release}
Provides:        kernel-modules-core  = %{version}-%{release}

%description
Mainline kernel for %{PLATFORM_NAME}, packaged for standard Fedora systems with UEFI boot support

%prep
%autosetup -p1 -n sm8550-mainline-sheng-%{KERNEL_VER}

# 准备默认配置
cp %{SOURCE1} .config

%build
# ccache 配置
export CCACHE_DIR="${CCACHE_DIR:-$HOME/.ccache}"
export CCACHE_MAXSIZE="${CCACHE_MAXSIZE:-10G}"
export CCACHE_SLOPPINESS="file_macro,locale,time_macros"
export CCACHE_NOHASHDIR="true"
mkdir -p "$CCACHE_DIR"

# 移除既有的 CONFIG_LOCALVERSION，通过 make 命令的参数来控制它
sed -i '/^CONFIG_LOCALVERSION=/d' .config

# 确保没有 localversion 文件影响版本号
rm -f localversion*

make ARCH=arm64 CC="ccache clang" LLVM=1 olddefconfig
make ARCH=arm64 CC="ccache clang" LLVM=1 EXTRAVERSION="%{KERNEL_EXTRA_VER}" LOCALVERSION= -j%{?_smp_build_ncpus} Image Image.gz modules dtbs

%install

# 1. 安装内核模块
make ARCH=arm64 CC="ccache clang" LLVM=1 EXTRAVERSION="%{KERNEL_EXTRA_VER}" LOCALVERSION= \
    INSTALL_MOD_PATH=%{buildroot} \
    modules_install
# 清理冗余链接
rm -rf %{buildroot}/lib/modules/*/build
rm -rf %{buildroot}/lib/modules/*/source
# UsrMerge
mkdir -p %{buildroot}/usr
mv %{buildroot}/lib %{buildroot}/usr/

# 2. 安装内核镜像、System.map 和配置文件到 /boot 目录
install -Dm644 arch/arm64/boot/Image     %{buildroot}/boot/Image
install -Dm644 arch/arm64/boot/Image.gz  %{buildroot}/boot/Image.gz
install -Dm644 System.map                %{buildroot}/boot/System.map-%{KERNEL_FULL_VER}
install -Dm644 .config                   %{buildroot}/boot/config-%{KERNEL_FULL_VER}

# 3. 安装设备树文件 (DTB) 到 /boot
install -Dm644 arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    %{buildroot}/boot/sm8550-xiaomi-%{DEVICE_NAME}.dtb

# 4. 生成 Android boot.img
cat arch/arm64/boot/Image.gz arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb > Image.gz-dtb_%{DEVICE_NAME}
install -Dm644 Image.gz-dtb_%{DEVICE_NAME} %{buildroot}/boot/Image.gz-dtb_%{DEVICE_NAME}
mv Image.gz-dtb_%{DEVICE_NAME} zImage_%{DEVICE_NAME}

chmod +x %{SOURCE2}
%{SOURCE2} --kernel zImage_%{DEVICE_NAME} --cmdline "root=PARTLABEL=linux rootwait rw" --base 0x00000000 --kernel_offset 0x00008000 --tags_offset 0x01e00000 --pagesize 4096 --id -o %{_topdir}/BUILD/boot_%{DEVICE_NAME}_dualboot.img
%{SOURCE2} --kernel zImage_%{DEVICE_NAME} --cmdline "root=PARTLABEL=userdata rootwait rw" --base 0x00000000 --kernel_offset 0x00008000 --tags_offset 0x01e00000 --pagesize 4096 --id -o %{_topdir}/BUILD/boot_%{DEVICE_NAME}_singleboot.img

# 5. 生成 UKI EFI
ukify build \
    --linux=arch/arm64/boot/Image \
    --devicetree=arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    --cmdline="console=tty0 root=PARTLABEL=linux rootwait rw" \
    --output=%{_topdir}/BUILD/bootaa64.efi
install -Dm644 %{_topdir}/BUILD/bootaa64.efi %{buildroot}/boot/efi/EFI/BOOT/bootaa64.efi


%files
/boot/Image
/boot/Image.gz
/boot/Image.gz-dtb_%{DEVICE_NAME}
/boot/sm8550-xiaomi-%{DEVICE_NAME}.dtb
/boot/System.map-%{KERNEL_FULL_VER}
/boot/config-%{KERNEL_FULL_VER}
/usr/lib/modules/%{KERNEL_FULL_VER}
/boot/efi/EFI/BOOT/bootaa64.efi


%posttrans
set -e
depmod -a "%{KERNEL_FULL_VER}"

%postun

