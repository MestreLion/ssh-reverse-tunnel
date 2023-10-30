#!/usr/bin/env bash
#
# install-client.sh - SSH Socks Proxy source host installer
#
# This file is part of <https://github.com/MestreLion/ssh-reverse-tunnel>
# Copyright (C) 2023 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
#------------------------------------------------------------------------------
set -Eeuo pipefail  # exit on any error
trap '>&2 echo "error: line $LINENO, status $?: $BASH_COMMAND"' ERR
#------------------------------------------------------------------------------

autossh=

slug=ssh-socks-proxy  # sync with ssh-socks-proxy.template.*.conf
self=${0##*/}
here=$(dirname "$(readlink -f "$0")")

#------------------------------------------------------------------------------
user_home()   { getent passwd -- "${1:-$USER}" | cut -d: -f6; }
user_exists() { getent passwd -- "${1:-}" >/dev/null; }
is_root()     { (( EUID == 0 )); }
bold()        { tput bold; printf '%s' "$@"; tput sgr0; }
green()       { tput setaf 2; bold "$@"; printf '\n'; }
exists()      { type "$@" >/dev/null 2>&1; }
argerr()      { printf "%s: %s\n" "$self" "${1:-error}" >&2; usage 1; }
invalid()     { argerr "invalid ${2:-option}: ${1:-}"; }
usage()       {
	exec >&2
	echo "Set up a SSH Socks Proxy source host"
	echo "Usage: ${0##*/} [-a|--autossh]"
	echo "Example: ${0##*/} vps"
	exit "${1:-0}"
}
#------------------------------------------------------------------------------

for arg in "$@"; do [[ "$arg" == "-h" || "$arg" == "--help" ]] && usage ; done
while (($#)); do
	# shellcheck disable=SC2221,SC2222
	case "$1" in
	-a|--autossh) autossh='-autossh';;
	 *) invalid "$1";;
	esac
	shift || break
done

if is_root; then
	mode=system
	prefix=/etc
	service_dir=/etc/systemd/system
else
	mode=user
	xdg_config=${XDG_CONFIG_HOME:-$HOME/.config}
	xdg_data=${XDG_DATA_HOME:-$HOME/.local/share}
	# shellcheck disable=SC2174
	mkdir --parents --mode 0700 -- "$xdg_config" "$xdg_data"
	prefix=$xdg_config
	service_dir=$xdg_data/systemd/user
	unset xdg_config xdg_data
fi

systemctl_mode=(--"$mode")
base_dir=$prefix/$slug
template=$here/ssh-socks-proxy.template.$mode.conf
config=$base_dir/$slug.conf
key_type=ed25519
key_file=$base_dir/id_$key_type
comment=$slug@$(hostname --fqdn)
service=${slug}${autossh}

# install autossh if needed
if [[ "$autossh" ]] && ! exists autossh; then
	sudo apt-get install -y autossh
fi

# Create the tree
mkdir --parents -- "$base_dir" "$service_dir"

# Generate SSH keys
if ! [[ -f "$key_file" ]]; then
	ssh-keygen -a 100 -t ed25519 -f "$key_file" -N "" -C "$comment"
fi

# create systemd service
cp -- "$here"/"$service"@.service "$service_dir"

# create config file
cp --no-clobber -- "$template" "$config"
nano -- "$config"

echo
green "For each target host, connect as root (or a sudoer) and run:"
echo "git clone https://github.com/MestreLion/ssh-reverse-tunnel"
echo "ssh-reverse-tunnel/ssh-socks-proxy/install-server.sh '$(<"$key_file".pub)'"
echo
green "When you exit the SSH session you may start (and possibly enable) the services:"
echo systemctl "${systemctl_mode[@]}" start "$service@TARGET_HOST"
