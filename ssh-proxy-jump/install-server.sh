#!/usr/bin/env bash
#
# install-server - SSH Proxy Jump target host installer (user and sshd settings)
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
user=${2:-ssh-proxy-jump}

# Service account home prefix (its $HOME parent directory)
prefix=${3-/etc}

# Contact info (no commas or semi-colons)
contact=${4:-github.com/MestreLion/ssh-reverse-tunnel}
contact=${contact//:/}; contact=${contact//,/};

#------------------------------------------------------------------------------
home=$prefix/$user
file=$home/authorized_keys
useropts=(
	--system  # implies --shell /usr/sbin/nologin
	--group   # create its group, otherwise system users are put in nogroup
	--quiet   # no error if system user already exists
	--home "$home"  # default is /home/<USER> even for system users
	--gecos "SSH Proxy Jump service account,,,,$contact"
)
#------------------------------------------------------------------------------
user_home()   { getent passwd -- "${1:-$USER}" | cut -d: -f6; }
user_exists() { getent passwd -- "${1:-}" >/dev/null; }
escape()      { printf '%q' "$1"; }
#------------------------------------------------------------------------------

if [[ -z "$key" ]]; then
	echo "Sets up an SSH Proxy Jump target host" >&2
	echo "Usage: ${0##*/} SSH_PUBLIC_KEY_CONTENT" \
		"[USERNAME [HOME_PREFIX [CONTACT_INFO]]]" >&2
	exit 1
fi

# Create and setup up user
if ! user_exists "$user"; then sudo adduser "${useropts[@]}" -- "$user"; fi
home=$(user_home "$user")  # might be different than specified if already existed
sudo -u "$user" mkdir -p -- "${file%/*}"
if ! [[ -f "$file" ]] || ! grep -Fx -- "$key" "$file"; then
	sudo -u "$user" tee -a >/dev/null -- "$file" <<< "$key"
fi

# Tune sshd for proxy jumps
sudo tee -- /etc/ssh/sshd_config.d/00-ssh-proxy-jump.conf >/dev/null <<EOF
# SSH Proxy Jump settings
# https://github.com/MestreLion/ssh-reverse-tunnel
#
# All settings are optional, and limited to the ${user} service account:
# - Change default authorized_keys path
# - Improve stability by disconnecting unresponsive clients to free used ports,
#    so clients can re-connect the proxy.
# - Set options suitable for Proxy Jump servers.
# - Improve security by further restricting client permissions, as the connection
#    is only meant to to be used for proxy jumps.

Match User ${user}
	# Change from the default ~/.ssh/authorized_keys
	AuthorizedKeysFile     $(escape "${file#$home/}")

	# Disconnect if client is unresponsive for 3 * 15 = 45 seconds.
	# Time without data to check if client is alive. Default: 0, no check.
	ClientAliveInterval    15
	# Attempts for above check to fail before disconnecting. Default: already 3.
	ClientAliveCountMax     3

	# Security: Allow only pubkey authentication, disabling passwords
	AuthenticationMethods  publickey

	# Allow binding tunnels and forwarding agents (most likely already the default)
	GatewayPorts           yes
	AllowTcpForwarding     local
	AllowAgentForwarding   yes

	# Disable interactive sessions, for both convenience and security
	PermitTTY              no
EOF
