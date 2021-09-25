#!/usr/bin/python3
# Copyright 2011-2021 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""Univention IP Calculator for DNS records (IPv6 edition)."""

from __future__ import print_function

import sys
import ipaddress
import optparse
from univention import ipcalc


def parse_options():
	"""Parse command line options."""
	usage = '%prog --calcdns --ip <addr> --netmask <mask> --output <type>'
	epilog = 'Calculate network values from network address for DNS records.'
	parser = optparse.OptionParser(usage=usage, epilog=epilog)
	parser.add_option(
		'--ip', dest='address',
		help='IPv4 or IPv6 address')
	parser.add_option(
		'--netmask', dest='netmask',
		help='Netmask or prefix length')
	parser.add_option(
		'--output', dest='output',
		choices=('network', 'reverse', 'pointer'),
		help='Specify requested output type')
	parser.add_option(
		'--calcdns', dest='calcdns',
		action='store_true', default=False,
		help='Request to calcuale DNS record entries')
	(options, _args) = parser.parse_args()
	if not options.calcdns:
		parser.error('Only --calcdns is supported')
	if options.output is None:
		parser.error('missing --output')
	if options.address is None:
		parser.error('missing --ip')
	if options.netmask is None:
		parser.error('missing --netmask')
	return options


def main():
	"""Calculate IP address parameters-"""
	options = parse_options()
	try:
		ipaddress.ip_address(u'%s' % (options.address,))
		# use ip_interface for networks for py2 py3 compatability
		network = ipaddress.ip_interface(u'%s/%s' % (options.address, options.netmask))
	except ValueError as ex:
		sys.exit(ex)
	try:
		if isinstance(network, ipaddress.IPv6Interface):
			family = 'ipv6'
		elif isinstance(network, ipaddress.IPv4Interface):
			family = 'ipv4'
		func = getattr(ipcalc, 'calculate_%s_%s' % (family, options.output))
	except (NameError, AttributeError):
		sys.exit("Unknown address format")
	else:
		print(func(network))


if __name__ == "__main__":
	main()
