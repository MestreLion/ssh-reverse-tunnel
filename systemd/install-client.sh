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

host=${1:-}; shift
tunnels=( "$@" )

slug=ssh-reverse-tunnel
here=$(dirname "$(readlink -f "$0")")

#------------------------------------------------------------------------------
user_home()   { getent passwd -- "${1:-$USER}" | cut -d: -f6; }
user_exists() { getent passwd -- "${1:-}" >/dev/null; }
is_root()     { (( EUID == 0 )); }
#------------------------------------------------------------------------------

if [[ -z "$host" ]]; then
	echo "Sets up a client for SSH Reverse Tunnel" >&2
	echo "Usage: ${0##*/} SSH_HOST [SSH_TUNNEL(s)...]" >&2
	echo "Example: ${0##*/} '$slug@example.com -p 1234'" \
		"'*:22222:localhost:22' '*:33333:localhost:33'"
	exit 1
fi

if is_root; then
	service_dir=/etc/systemd/system
	prefix=/etc
else
	xdg_config=${XDG_CONFIG_HOME:-$HOME/.config}
	xdg_data=${XDG_DATA_HOME:-$HOME/.local/share}
	# shellcheck disable=SC2174
	mkdir --parents --mode 0700 -- "$xdg_config" "$xdg_data"
	prefix=$xdg_config
	service_dir=$xdg_data/systemd/user
	unset xdg_config xdg_data
fi

base_dir=$prefix/$slug
service_file=$service_dir/$slug.service
key_type=ed25519
key_file=$base_dir/id_$key_type
comment=$slug@$(hostname --fqdn)

# Create the tree
mkdir -parents -- "$base_dir" "$service_dir"

# Generate SSH keys
if ! [[ -f "$key_file" ]]; then
	ssh-keygen -a 100 -t ed25519 -f "$key_file" -C "$comment"
fi

# create systemd service
if [[ -f "$service_file" ]]; then exit; fi

tunnel_str=$(printf '-R %s  \\\n\t' "${tunnels[@]}")
awk -F'\t' -v tunnels="$tunnel_str" -v host="$host" -- \
	'/localhost/{sub(tunnels)}/example/{sub(host)' \
	"$here"/ssh-reverse-tunnel.service > "$service_file"
