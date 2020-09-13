SSH Reverse Tunnel Icons
========================

Icons for connection status based on [Gnome Icon Theme](https://download.gnome.org/sources/gnome-icon-theme),
using `/src/media-record.svg` as a template file, copied from
[Debian git repository commit `532e3019`](https://salsa.debian.org/gnome-team/gnome-icon-theme/-/commit/532e3019a19e16995e4e1087b49c4c38d4b4a7b6)
before it was eventually [replaced](https://salsa.debian.org/gnome-team/gnome-icon-theme/-/commit/e69dde29fb4fe4beb17db5271fe5e3cb14a076f6)
by `src/media-control-icons.svg` which aggregates all media control icons since 2010.


That template file was extensively modified to rectify its elements alignment and
also reduce both complexity and file size.

Colors
-------
**HSV**
H is 0, 90, 45 for Red, Geen, Yellow icons
S,V for each gradient is:
220,140
221,106
255, 82
(except for Gray, which S=0)

Red (original)
#ef2929
#c60e0e
#a40000

Green:
#0ec624
#28ef40
#00a413

Yellow:
#e3ef29
#bbc60e
#9aa400

Gray:
#8c8c8c
#6a6a6a
#525252


Tech Details
-------------
from gnome-icon-theme project (does not seem to have a website)
https://salsa.debian.org/gnome-team/gnome-icon-theme

https://download.gnome.org/sources/gnome-icon-theme/2.28/gnome-icon-theme-2.28.0.tar.bz2
https://download.gnome.org/sources/gnome-icon-theme/3.12/gnome-icon-theme-3.12.0.tar.xz

scalable/actions/media-record.svg
Single 48x48 SVG
Created:	9f733f86e942d815bf2408128c0b5985e0d4f899	Aug 13 18:52:42 2007 +0000	new media actions icons and various touchups.	Lapo Calamandrei <lapo@src.gnome.org>
Last modified:	d517bcb97556944d70df473d803523e62454bcd6	Aug 27 23:35:16 2007 +0000	Add missing .icon.in files	Rodney Dawes <dobey.pwns@gmail.com>
Last Release:	6eca6e1cf3fb8a38d6a0956b039378bc844c6740	Sep 21 21:45:25 2009 -0400	Release 2.28.0	Rodney Dawes <dobey@gnome.org>
Deleted:	fd88a47bba6ee8c0419f9f97ce8c619e23babe89	Oct 13 20:25:35 2009 +0200	use moblin-style 'build system'	Jakub Steiner <jimmac@gmail.com>

src/media-record.svg
One canvas containing 4 images in a single svg: 48, 32, 22, 16
Never released
Created:	532e3019a19e16995e4e1087b49c4c38d4b4a7b6	Jul  5 20:22:40 2009 +0100	Automatic move of all icons to the one canvas workflow.	Benjamin Berg <benjamin@sipsolutions.net>
Deleted:	e69dde29fb4fe4beb17db5271fe5e3cb14a076f6	Jan 27 16:10:22 2010 +0100	Aggregated media icons.	Lapo Calamandrei <calamandrei@gmail.com>

src/media-icons.svg	src/media-control-icons.svg
One canvas containing all media control (play, pause, stop, record, etc) in all 4 sizes.
Created:	e69dde29fb4fe4beb17db5271fe5e3cb14a076f6	Jan 27 16:10:22 2010 +0100	Aggregated media icons.	Lapo Calamandrei <calamandrei@gmail.com>
Renamed:	3f67c74d7e19ea1a3d0596154b5ba2eca2b0f54b	Jan 27 16:14:35 2010 +0100	media-control-icons sounds saner.	Lapo Calamandrei <calamandrei@gmail.com>
Last Modified:	a2eccba0a0b8e74262b4ae650f6c68b09285e6ce	Oct 19 12:01:37 2011 +0200	media-playback-start is not rtl by default	Jakub Steiner <jimmac@gmail.com>
Last Release:	a5d6b00da2edf22913305e9af337c4fe797eb11a	Mar 25 00:36:33 2014 -0400	3.12.0	Matthias Clasen <mclasen@redhat.com>
Last Debian:	a739d8c3f2966d4d2c56c21117931a367a5cba06	Mar 17 22:47:26 2018 -0400	releasing package gnome-icon-theme version 3.12.0-3	Jeremy Bicha <jbicha@ubuntu.com>

SVG minifyers:
https://vecta.io/nano
https://jakearchibald.github.io/svgomg/
https://kraken.io/web-interface
https://www.iloveimg.com/resize-image/resize-svg
https://www.svgminify.com/
