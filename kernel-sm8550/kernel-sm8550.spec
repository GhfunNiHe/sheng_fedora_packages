%undefine        _debugsource_packages
%global KERNEL_VER 7.2.2
%global KERNEL_TAG 7.2.2
%global KERNEL_RPMVER 7.2.2
%global DEVICE_NAME sheng
%global PLATFORM_NAME sm8550

Version:         %{KERNEL_RPMVER}
Release:         2.%{DEVICE_NAME}%{?dist}
ExclusiveArch:  aarch64
Name:            kernel-%{PLATFORM_NAME}
Summary:         Mainline Linux kernel for %{PLATFORM_NAME} devices
License:         GPLv2
URL:             https://github.com/ianchb/sm8550-mainline

Source0:         %{url}/archive/%{KERNEL_TAG}.tar.gz
Source1:         https://github.com/ianchb/sm8550-mainline/releases/download/%{KERNEL_VER}/sm8550.config
Source2:         scripts/mkbootimg
Source3:         extra-sm8550.config
Source4:         ukify.conf
Source5:         99-sheng-generic.conf

BuildRequires:   bc bison dwarves diffutils elfutils-devel findutils git-core hmaccalc hostname make openssl-devel perl-interpreter rsync tar which flex bzip2 xz zstd python3 python3-devel python3-pyyaml rust rust-src bindgen rustfmt clippy opencsd-devel net-tools
BuildRequires:   clang lld llvm ccache systemd-boot-unsigned systemd-ukify

Provides:        kernel               = %{version}-%{release}
Provides:        kernel-core          = %{version}-%{release}
Provides:        kernel-modules       = %{version}-%{release}
Provides:        kernel-modules-core  = %{version}-%{release}
Requires:        dracut
Requires:        systemd-ukify
Requires:        systemd-boot-unsigned

%description
Mainline kernel for %{PLATFORM_NAME}, packaged for standard Fedora systems
with UEFI boot support. Built from source archive with commit hash resolved
from the upstream tag (e.g. %{KERNEL_VER}-%{PLATFORM_NAME}-gXXXXXXXXX).

%prep
%setup -q -n sm8550-mainline-%{KERNEL_TAG}

# Resolve tag to commit hash without full clone
COMMIT_HASH=$(git ls-remote %{url}.git refs/tags/%{KERNEL_TAG} | awk '{print $1}' | cut -c1-7)
echo "Tag %{KERNEL_TAG} commit: ${COMMIT_HASH}"
LOCALVERSION_FULL="-%{PLATFORM_NAME}-g${COMMIT_HASH}"
echo "${LOCALVERSION_FULL}" > .lkv_suffix

cp %{SOURCE1} .config
sed -i '/^CONFIG_LOCALVERSION=/d' .config
sed -i 's/^CONFIG_LOCALVERSION_AUTO=y/CONFIG_LOCALVERSION_AUTO=n/' .config

# Append extra config (zswap support); make olddefconfig normalizes it
cat %{SOURCE3} >> .config

%build
LOCALVERSION_FULL=$(cat .lkv_suffix)

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
LOCALVERSION_FULL=$(cat .lkv_suffix)

# 1. Install modules
make ARCH=arm64 CC="ccache clang" LLVM=1 LOCALVERSION="${LOCALVERSION_FULL}" \
    INSTALL_MOD_PATH=%{buildroot} modules_install
rm -rf %{buildroot}/lib/modules/*/build
rm -rf %{buildroot}/lib/modules/*/source
# UsrMerge
mkdir -p %{buildroot}/usr
mv %{buildroot}/lib %{buildroot}/usr/

# 2. Install kernel image, System.map, and config to /boot. These are
#    versioned so multiple kernel versions can coexist; booting happens via
#    the flashed boot.img, not these /boot files.
install -Dm644 arch/arm64/boot/Image     %{buildroot}/boot/Image-${KERNEL_RELEASE}
install -Dm644 arch/arm64/boot/Image     %{buildroot}/boot/vmlinuz-${KERNEL_RELEASE}
install -Dm644 arch/arm64/boot/Image.gz  %{buildroot}/boot/Image.gz-${KERNEL_RELEASE}
install -Dm644 System.map                %{buildroot}/boot/System.map-${KERNEL_RELEASE}
install -Dm644 .config                   %{buildroot}/boot/config-${KERNEL_RELEASE}

# 3. Install device tree
install -Dm644 arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    %{buildroot}/boot/sm8550-xiaomi-%{DEVICE_NAME}-${KERNEL_RELEASE}.dtb
install -Dm644 arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    %{buildroot}/usr/lib/modules/${KERNEL_RELEASE}/dtb/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb

# 4. Generate boot.img (Debian-style: outside of kernel tree, image.gz + dtb first)
cat arch/arm64/boot/Image.gz \
    arch/arm64/boot/dts/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb \
    > Image.gz-dtb_%{DEVICE_NAME}
install -Dm644 Image.gz-dtb_%{DEVICE_NAME} \
    %{buildroot}/boot/Image.gz-dtb_%{DEVICE_NAME}-${KERNEL_RELEASE}
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

# 6. Install UKI/dracut config (consumed by %posttrans)
install -Dm644 %{SOURCE4} %{buildroot}%{_sysconfdir}/systemd/ukify.conf
install -Dm644 %{SOURCE5} %{buildroot}%{_sysconfdir}/dracut.conf.d/99-sheng-generic.conf

%files
/boot/Image-*
/boot/Image.gz-*
/boot/Image.gz-dtb_%{DEVICE_NAME}-*
/boot/sm8550-xiaomi-%{DEVICE_NAME}-*.dtb
/boot/vmlinuz-*
/boot/System.map-*
/boot/config-*
/usr/lib/modules/*
%config(noreplace) %{_sysconfdir}/systemd/ukify.conf
%config(noreplace) %{_sysconfdir}/dracut.conf.d/99-sheng-generic.conf

%pre
# Clean up old kernel files from previous version on upgrade
if [ -f /usr/lib/modules/.kernel-version ]; then
    OLD_KVER=$(cat /usr/lib/modules/.kernel-version)
    if [ -n "$OLD_KVER" ]; then
        rm -rf "/usr/lib/modules/$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/System.map-$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/config-$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/vmlinuz-$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/initramfs-$OLD_KVER.img" 2>/dev/null || :
        rm -f "/boot/efi/EFI/fedora/fedora-$OLD_KVER.efi" 2>/dev/null || :
        rm -f "/boot/Image-$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/Image.gz-$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/Image.gz-dtb_%{DEVICE_NAME}-$OLD_KVER" 2>/dev/null || :
        rm -f "/boot/sm8550-xiaomi-%{DEVICE_NAME}-$OLD_KVER.dtb" 2>/dev/null || :
    fi
fi

%posttrans
set -e

# Determine the newly installed kernel version from the modules directory.
# %pre removed the previous kernel's modules, so the newest (and only) left
# is this package's own. .kernel-version is intentionally not in %files so
# multiple kernel versions do not claim the same file.
KERNEL_RELEASE=$(ls -dt /usr/lib/modules/*/ 2>/dev/null | head -1 | sed 's#/$##; s#.*/##')
if [ -z "$KERNEL_RELEASE" ]; then
    echo "CRITICAL: no kernel modules directory found" >&2
    exit 1
fi
echo "${KERNEL_RELEASE}" > /usr/lib/modules/.kernel-version

# 1. Build module dependencies for the new kernel
depmod -a "${KERNEL_RELEASE}"

echo "--- Generating UKI for ${KERNEL_RELEASE} using dracut + ukify ---"

UKI_DIR="/boot/efi/EFI/fedora"
INITRD_PATH="/boot/initramfs-${KERNEL_RELEASE}.img"
KERNEL_PATH="/boot/vmlinuz-${KERNEL_RELEASE}"
DTB_PATH="/usr/lib/modules/${KERNEL_RELEASE}/dtb/qcom/sm8550-xiaomi-%{DEVICE_NAME}.dtb"
UKI_OUTPUT_PATH="${UKI_DIR}/fedora-${KERNEL_RELEASE}.efi"
mkdir -p "${UKI_DIR}"

# 2. Generate initramfs with dracut (reads /etc/dracut.conf.d/)
dracut --kver "${KERNEL_RELEASE}" --force
if [ ! -f "${INITRD_PATH}" ]; then
    echo "CRITICAL: dracut failed to generate initramfs at ${INITRD_PATH}" >&2
    exit 1
fi
echo "Initramfs generated at ${INITRD_PATH}"

# 3. Assemble the UKI with systemd-ukify. Static config (Cmdline/Stub) is read
#    from /etc/systemd/ukify.conf, which this package installs.
if [ ! -f /usr/lib/systemd/boot/efi/linuxaa64.efi.stub ]; then
    echo "CRITICAL: EFI stub /usr/lib/systemd/boot/efi/linuxaa64.efi.stub missing (install systemd-boot-unsigned)" >&2
    exit 1
fi
ukify build \
    --linux="${KERNEL_PATH}" \
    --initrd="${INITRD_PATH}" \
    --devicetree="${DTB_PATH}" \
    --output="${UKI_OUTPUT_PATH}"

if [ ! -f "${UKI_OUTPUT_PATH}" ]; then
    echo "CRITICAL: ukify failed to generate UKI at ${UKI_OUTPUT_PATH}" >&2
    rm -f "${INITRD_PATH}"
    exit 1
fi
echo "SUCCESS: UKI generated at ${UKI_OUTPUT_PATH}"

# 4. Remove the standalone initramfs; only the UKI is kept
rm -f "${INITRD_PATH}"

echo "--- UKI generation complete for ${KERNEL_RELEASE} ---"
