#!/usr/bin/env bash
#
# install-server - SSH Reverse Tunnel server installer (user and sshd settings)
#
# This file is part of <https://github.com/MestreLion/ssh-reverse-tunnel>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
#------------------------------------------------------------------------------
set -Eeuo pipefail  # exit on any error
trap '>&2 echo "error: line $LINENO, status $?: $BASH_COMMAND"' ERR
#------------------------------------------------------------------------------

# SSH Public Key content
key=${1:-}

# Service account username
user=${2:-ssh-reverse-tunnel}

# Service account home prefix (its $HOME parent directory)
prefix=${3-/var/lib}

# Contact info (no commas or semi-colons)
contact=${4:-github.com/MestreLion/ssh-reverse-tunnel}
contact=${contact//:/}; contact=${contact//,/};

# Also no commas or semi-colons
fullname='SSH Reverse Tunnel service account'

#------------------------------------------------------------------------------
home=$prefix/$user
file=$home/authorized_keys
gecos="${fullname},,,,${contact}"
useropts=(
	--system  # implies --shell /usr/sbin/nologin
	--group   # create its group, otherwise system users are put in nogroup
	--quiet   # no error if system user already exists
	--home "$home"  # default is /home/<USER> even for system users
	--gecos "$gecos"
)
#------------------------------------------------------------------------------
user_home()   { getent passwd -- "${1:-$USER}" | cut -d: -f6; }
user_exists() { getent passwd -- "${1:-}" >/dev/null; }
escape()      { printf '%q' "$1"; }
usage() {
	local status=${1:-0}
	if ((status)); then exec >&2; fi
	echo "Sets up a server for SSH Reverse Tunnel"
	echo "Usage: ${0##*/} SSH_PUBLIC_KEY_CONTENT" \
		"[USERNAME [HOME_PREFIX [CONTACT_INFO]]]"
	exit "$status"
}
#------------------------------------------------------------------------------

for arg in "$@"; do [[ "$arg" == "-h" || "$arg" == "--help" ]] && usage; done
if [[ -z "$key" ]]; then
	echo "Error: Argument SSH_PUBLIC_KEY_CONTENT is missing" >&2
	usage 1
fi

# Create and setup up user
if user_exists "$user"; then
	if [[ "$(user_home "$user")" != "$home" ]]; then
		echo "User $user already exists, moving its HOME to $home"
		sudo pkill -u "$user"
		sudo usermod --home "$home" --move-home --comment "$gecos"
		home=$(user_home "$user")
	fi
else
	sudo adduser "${useropts[@]}" -- "$user"
fi
if ! sudo -u "$user" grep -qFx -- "$key" "$file"; then
	sudo -u "$user" mkdir -p -- "${file%/*}"
	sudo -u "$user" tee -a >/dev/null -- "$file" <<< "$key"
fi

# Make sure file exists with propoer permissions
sudo -u "$user" touch -- "$file"
sudo -u "$user" chmod 600 -- "$file"

# Add $prefix to snapd to avoid snapd-desktop-integration apparmor audit errors
# '/home' is always included, '/etc' is not allowed
# See https://snapcraft.io/docs/home-outside-home
if ! [[ "$prefix" == /home ]] && ! [[ "$prefix" == /etc ]]; then
	sudo snap set system homedirs="$prefix"
fi

# Tune sshd for reverse tunnels
sudo tee -- /etc/ssh/sshd_config.d/10-ssh-reverse-tunnel.conf >/dev/null <<EOF
# SSH Reverse Tunnel server settings
# https://github.com/MestreLion/ssh-reverse-tunnel
#
# All settings are optional, and limited to the ${user} service account:
# - Change default authorized_keys path
# - Improve stability by disconnecting unresponsive clients to free used ports,
#    so clients can re-connect and re-create the tunnels.
# - Improve security by further restricting client permissions, as the connection
#    is only meant to set up the reverse tunnels.
# - Improve tunnels' capabilities, allowing to bind ports to external interfaces

Match User ${user}
	# Configurable and not bound to be the default ~/.ssh/authorized_keys
	# Relative to the user's HOME $(escape "$home")
	AuthorizedKeysFile     $(escape "${file#$home/}")

	# Disconnect if client is unresponsive for 3 * 15 = 45 seconds.
	# Time without data to check if client is alive. Default: 0, no check.
	ClientAliveInterval    15
	# Attempts for above check to fail before disconnecting. Default: already 3.
	ClientAliveCountMax     3

	# Security: disable agent, restrict to pubkey, disable interactive sessions
	AllowAgentForwarding   no
	AuthenticationMethods  publickey
	PermitTTY              no
EOF
