SSH Reverse Tunnel `systemd` services
=====================================

* Recommended _client_ install (tunnel origin, where the service actually runs),
  as a user with `sudo` priviledges so it installs as `systemd` _system_ services
  with configuration at `/etc/ssh-reverse-tunnel`:

```sh
git clone -- https://github.com/MestreLion/ssh-reverse-tunnel.git ~/install/ssh-reverse-tunnel
sudo install/ssh-reverse-tunnel/systemd/install-client.sh [SERVER_ALIAS...]
```

Take note of the generated SSH public key, install `ssh-reverse-tunnel` on the
needed servers (see instructions below), then start the services:

```sh
sudo systemctl start ssh-reverse-tunnel@*.service
```

---

* Recommended _server_ install (tunnel destination, creating the `ssh-reverse-tunnel` user),
  also as a user with `sudo` priviledges:

```sh
keys='
ssh-ed25519 AAA...XXX ssh-reverse-tunnel@client_a.example.com
ssh-ed25519 BBB...XXX ssh-reverse-tunnel@client_b.example.com
ssh-ed25519 CCC...XXX ssh-reverse-tunnel@client_c.example.com
'
git -C "$HOME" clone -- 'https://github.com/MestreLion/ssh-reverse-tunnel' || true
sudo "$HOME"/ssh-reverse-tunnel/systemd/install-server.sh "dummy"
sed '/^$/d' <<< "$keys" | sudo tee /etc/ssh-reverse-tunnel/authorized_keys >/dev/null
```
