#!/usr/bin/env bash
#
# install-server - SSH Reverse Tunnel server installer
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

#------------------------------------------------------------------------------
home=$prefix/$user
file=$home/.ssh/authorized_keys
useropts=(
	--system  # implies --shell /usr/sbin/nologin
	--group   # create its group, otherwise system users are put in nogroup
	--quiet   # no error if system user already exists
	--home "$home"  # default /home/<USER> even for system users
	--gecos "SSH Reverse Tunnel service account,,,,$contact"
)
#------------------------------------------------------------------------------
user_home()   { getent passwd -- "${1:-$USER}" | cut -d: -f6; }
user_exists() { getent passwd -- "${1:-}" >/dev/null; }
#------------------------------------------------------------------------------

if [[ -z "$key" ]]; then
	exec &2
	echo "Sets up a server for SSH Reverse Tunnel" >&2
	echo "Usage: ${0##*/} SSH_PUBLIC_KEY_CONTENT" \
		"[USERNAME [HOME_PREFIX [CONTACT_INFO]]]" >&2
	exit 1
fi

if ! user_exists "$user"; then sudo adduser "${useropts[@]}" -- "$user"; fi
home=$(user_home "$user")  # might be different than specified if already existed
sudo -u "$user" mkdir -pm 0700 -- "${file%/*}"
if ! [[ -f "$file" ]] || ! grep -Fx -- "$key" "$file"; then
	sudo -u "$user" tee -a -- "$file" <<< "$key"
fi
sudo -u "$user" chmod 0600 -- "$file"
