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
ExclusiveArch:   aarch64
Name:            kernel-%{PLATFORM_NAME}
Summary:         Mainline Linux kernel for %{PLATFORM_NAME} devices
License:         GPLv2
URL:             https://github.com/ianchb/sm8550-mainline
Source0:         %{url}/archive/sheng-%{KERNEL_VER}.tar.gz
Source1:         https://github.com/ianchb/sm8550-mainline/releases/download/%{KERNEL_VER}/sm8550.config
Source2:         scripts/mkbootimg

BuildRequires:   bc bison dwarves diffutils elfutils-devel findutils git-core hmaccalc hostname make openssl-devel perl-interpreter rsync tar which flex bzip2 xz zstd python3 python3-devel python3-pyyaml rust rust-src bindgen rustfmt clippy opencsd-devel net-tools dracut
BuildRequires:   clang lld llvm ccache

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
# INSTALL_MOD_PATH 指向 %{buildroot}/usr，这会将模块安装到 %{buildroot}/usr/lib/modules/%{KERNEL_FULL_VER}/
make ARCH=arm64 CC="ccache clang" LLVM=1 EXTRAVERSION="%{KERNEL_EXTRA_VER}" LOCALVERSION= \
    INSTALL_MOD_PATH=%{buildroot}/usr \
    modules_install

# 2. 安装内核镜像、System.map 和配置文件到 /boot 目录
install -Dm644 arch/arm64/boot/Image %{buildroot}/boot/vmlinuz-%{KERNEL_FULL_VER}
install -Dm644 System.map %{buildroot}/boot/System.map-%{KERNEL_FULL_VER}
install -Dm644 .config    %{buildroot}/boot/config-%{KERNEL_FULL_VER}

# 3. 安装设备树文件 (DTB)
install -d %{buildroot}/usr/lib/modules/%{KERNEL_FULL_VER}/dtb/qcom
install -Dm644 arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb %{buildroot}/usr/lib/modules/%{KERNEL_FULL_VER}/dtb/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb

# 4. 生成 Android boot.img
cat arch/arm64/boot/Image.gz arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb > Image.gz-dtb_%{DEVICE_NAME}
mv Image.gz-dtb_%{DEVICE_NAME} zImage_%{DEVICE_NAME}

chmod +x %{SOURCE2}
%{SOURCE2} --kernel zImage_%{DEVICE_NAME} --cmdline "root=PARTLABEL=linux rootwait rw" --base 0x00000000 --kernel_offset 0x00008000 --tags_offset 0x01e00000 --pagesize 4096 --id -o boot_%{DEVICE_NAME}_dualboot.img
%{SOURCE2} --kernel zImage_%{DEVICE_NAME} --cmdline "root=PARTLABEL=userdata rootwait rw" --base 0x00000000 --kernel_offset 0x00008000 --tags_offset 0x01e00000 --pagesize 4096 --id -o boot_%{DEVICE_NAME}_singleboot.img


%files
/boot/vmlinuz-%{KERNEL_FULL_VER}
/boot/System.map-%{KERNEL_FULL_VER}
/boot/config-%{KERNEL_FULL_VER}
/usr/lib/modules/%{KERNEL_FULL_VER}


%posttrans
# ==============================================================================
# This script runs after the package's files are installed.
# It drives the UKI generation process. Static config is read from files,
# while version-specific paths are passed as arguments for robustness.
# ==============================================================================
set -e

KERNEL_FULL_VER="%{KERNEL_FULL_VER}"
DEVICE_NAME="%{DEVICE_NAME}"

# --- 为新内核生成模块依赖 ---
depmod -a "${KERNEL_FULL_VER}"


echo "--- Generating UKI for ${KERNEL_FULL_VER} using dracut + ukify ---"

# --- 定义路径 ---
UKI_DIR="/boot/efi/EFI/fedora"
INITRD_PATH="/boot/initramfs-${KERNEL_FULL_VER}.img"
KERNEL_PATH="/boot/vmlinuz-${KERNEL_FULL_VER}"
DTB_PATH="/usr/lib/modules/${KERNEL_FULL_VER}/dtb/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb"

UKI_OUTPUT_PATH="${UKI_DIR}/fedora-${KERNEL_FULL_VER}.efi"
mkdir -p "$UKI_DIR"

# --- 步骤 1: 使用 dracut 生成 initramfs ---
echo "Generating initramfs with dracut..."
# dracut 会从 /etc/dracut.conf.d/ 读取配置
dracut --kver "${KERNEL_FULL_VER}" --force
if [ ! -f "${INITRD_PATH}" ]; then
    echo "CRITICAL: dracut failed to generate initramfs at ${INITRD_PATH}" >&2
    exit 1
fi
echo "Initramfs generated at ${INITRD_PATH}"

# --- 步骤 2: 使用 systemd-ukify 生成 UKI ---
echo "Generating UKI with systemd-ukify..."
# ukify 会从 /etc/systemd/ukify.conf 读取静态配置 (Cmdline, Stub)
# 我们为确保健壮性，直接提供版本相关的路径。
ukify build \
    --linux="${KERNEL_PATH}" \
    --initrd="${INITRD_PATH}" \
    --devicetree="${DTB_PATH}" \
    --output="${UKI_OUTPUT_PATH}"

if [ ! -f "${UKI_OUTPUT_PATH}" ]; then
    echo "CRITICAL: ukify failed to generate UKI at ${UKI_OUTPUT_PATH}" >&2
    # 清理失败的中间产物
    rm -f "${INITRD_PATH}"
    exit 1
fi
echo "SUCCESS: UKI generated at ${UKI_OUTPUT_PATH}"

# --- 步骤 3: 清理独立的 initramfs ---
echo "Cleaning up standalone initramfs..."
rm -f "${INITRD_PATH}"

echo "--- UKI generation complete for ${KERNEL_FULL_VER} ---"

%postun

