import jgns_deps
from pathlib import Path

cryptsetup = Path(jgns_deps.cryptsetup) / "bin/cryptsetup"
dd = Path(jgns_deps.coreutils) / "bin/dd"
free = Path(jgns_deps.procps_ng) / "bin/free"
gdisk = Path(jgns_deps.gptfdisk) / "bin/gdisk"
lvcreate = Path(jgns_deps.lvm2) / "bin/lvcreate"
mkdir = Path(jgns_deps.coreutils) / "bin/mkdir"
mkfs_ext4 = Path(jgns_deps.e2fsprogs) / "bin/mkfs.ext4"
mkfs_fat = Path(jgns_deps.dosfstools) / "bin/mkfs.fat"
mkswap = Path(jgns_deps.utillinux) / "bin/mkswap"
mount = Path(jgns_deps.utillinux) / "bin/mount"
openssl = Path(jgns_deps.openssl) / "bin/openssl"
pvcreate = Path(jgns_deps.lvm2) / "bin/pvcreate"
rsync = Path(jgns_deps.rsync) / "bin/rsync"
stow = Path(jgns_deps.stow) / "bin/stow"
sudo = Path(jgns_deps.coreutils) / "bin/sudo"
swapon = Path(jgns_deps.utillinux) / "bin/swapon"
vgcreate = Path(jgns_deps.lvm2) / "bin/vgcreate"

# These are special -- we want to use the "system"
# version of these commands.
nix_env = "nix-env"
nix_channel = "nix-channel"
nixos_rebuild = "nixos-rebuild"
