%undefine        _debugsource_packages
%global KERNEL_VER 7.1.5
%global DEVICE_NAME sheng
%global PLATFORM_NAME sm8550

# Kernel will be built as: 7.1.5-sm8550-gXXXXXXXXX
%global LOCALVERSION -%{PLATFORM_NAME}

Version:         %{KERNEL_VER}.%{PLATFORM_NAME}
Release:         1.%{DEVICE_NAME}%{?dist}
ExclusiveArch:  aarch64
Name:            kernel-%{PLATFORM_NAME}
Summary:         Mainline Linux kernel for %{PLATFORM_NAME} devices
License:         GPLv2
URL:             https://github.com/ianchb/sm8550-mainline

# Source0 kept for spectool compatibility; actual source fetched via git clone in %prep
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
Mainline kernel for %{PLATFORM_NAME}, packaged for standard Fedora systems
with UEFI boot support. Built from git to include the commit hash in the
kernel version (e.g. %{KERNEL_VER}%{LOCALVERSION}-gXXXXXXXXX).

%prep
git clone --branch sheng-%{KERNEL_VER} --depth 1 %{url}.git kernel

cd kernel
cp %{SOURCE1} .config

%build
cd kernel

# Append git hash to LOCALVERSION (no commit count)
GIT_HASH=$(git rev-parse --short=12 HEAD)
LOCALVERSION_FULL="%{LOCALVERSION}-g${GIT_HASH}"

export CCACHE_DIR="${CCACHE_DIR:-$HOME/.ccache}"
export CCACHE_MAXSIZE="${CCACHE_MAXSIZE:-10G}"
export CCACHE_SLOPPINESS="file_macro,locale,time_macros"
export CCACHE_NOHASHDIR="true"
mkdir -p "$CCACHE_DIR"

make ARCH=arm64 CC="ccache clang" LLVM=1 LOCALVERSION="${LOCALVERSION_FULL}" olddefconfig
make ARCH=arm64 CC="ccache clang" LLVM=1 LOCALVERSION="${LOCALVERSION_FULL}" \
    -j%{?_smp_build_ncpus} Image Image.gz modules dtbs

# Save the full kernel version for %%install
echo "%{KERNEL_VER}${LOCALVERSION_FULL}" > %{_topdir}/BUILD/kernel-version

%install
KERNEL_RELEASE=$(cat %{_topdir}/BUILD/kernel-version)
GIT_HASH=$(cd kernel && git rev-parse --short=12 HEAD)
LOCALVERSION_FULL="%{LOCALVERSION}-g${GIT_HASH}"
cd kernel

# 1. Install modules
make ARCH=arm64 CC="ccache clang" LLVM=1 LOCALVERSION="${LOCALVERSION_FULL}" \
    INSTALL_MOD_PATH=%{buildroot} modules_install
rm -rf %{buildroot}/lib/modules/*/build
rm -rf %{buildroot}/lib/modules/*/source
# UsrMerge
mkdir -p %{buildroot}/usr
mv %{buildroot}/lib %{buildroot}/usr/

# 2. Install kernel image, System.map, and config to /boot
install -Dm644 arch/arm64/boot/Image     %{buildroot}/boot/Image
install -Dm644 arch/arm64/boot/Image.gz  %{buildroot}/boot/Image.gz
install -Dm644 System.map                %{buildroot}/boot/System.map-${KERNEL_RELEASE}
install -Dm644 .config                   %{buildroot}/boot/config-${KERNEL_RELEASE}

# 3. Install device tree
install -Dm644 arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    %{buildroot}/boot/sm8550-xiaomi-%{DEVICE_NAME}.dtb

# 4. Generate boot.img (Debian-style: outside of kernel tree, image.gz + dtb first)
cat arch/arm64/boot/Image.gz \
    arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    > Image.gz-dtb_%{DEVICE_NAME}
install -Dm644 Image.gz-dtb_%{DEVICE_NAME} %{buildroot}/boot/Image.gz-dtb_%{DEVICE_NAME}
mv Image.gz-dtb_%{DEVICE_NAME} zImage_%{DEVICE_NAME}

chmod +x %{SOURCE2}
%{SOURCE2} --kernel zImage_%{DEVICE_NAME} \
    --cmdline "root=PARTLABEL=linux rootwait rw" \
    --base 0x00000000 --kernel_offset 0x00008000 \
    --tags_offset 0x01e00000 --pagesize 4096 --id \
    -o %{_topdir}/BUILD/boot_%{DEVICE_NAME}_dualboot.img
%{SOURCE2} --kernel zImage_%{DEVICE_NAME} \
    --cmdline "root=PARTLABEL=userdata rootwait rw" \
    --base 0x00000000 --kernel_offset 0x00008000 \
    --tags_offset 0x01e00000 --pagesize 4096 --id \
    -o %{_topdir}/BUILD/boot_%{DEVICE_NAME}_singleboot.img

# 5. Generate UKI EFI
ukify build \
    --linux=arch/arm64/boot/Image \
    --devicetree=arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    --cmdline="console=tty0 root=PARTLABEL=linux rootwait rw" \
    --output=%{_topdir}/BUILD/bootaa64.efi
install -Dm644 %{_topdir}/BUILD/bootaa64.efi \
    %{buildroot}/boot/efi/EFI/BOOT/bootaa64.efi

# 6. Save kernel version for %%posttrans
echo "${KERNEL_RELEASE}" > %{buildroot}/usr/lib/modules/.kernel-version

%files
/boot/Image
/boot/Image.gz
/boot/Image.gz-dtb_%{DEVICE_NAME}
/boot/sm8550-xiaomi-%{DEVICE_NAME}.dtb
/boot/System.map-*
/boot/config-*
/usr/lib/modules/*
/boot/efi/EFI/BOOT/bootaa64.efi

%posttrans
KVER=$(cat /usr/lib/modules/.kernel-version 2>/dev/null)
if [ -n "$KVER" ] && [ -d "/usr/lib/modules/$KVER" ]; then
    depmod -a "$KVER"
elif [ -d /usr/lib/modules ]; then
    # Fallback: use the last module directory
    for d in /usr/lib/modules/*/kernel; do
        [ -d "$d" ] || continue
        k=$(basename "$(dirname "$d")")
        depmod -a "$k" 2>/dev/null || :
    done
fi
