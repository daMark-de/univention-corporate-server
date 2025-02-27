# -*- coding: utf-8 -*-
#
# Copyright 2004-2021 Univention GmbH
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

"""
|UDM| module for Organizational Unit containers
"""

from univention.admin.layout import Tab, Group
from univention.admin import configRegistry
import univention.admin.uldap
import univention.admin.syntax
import univention.admin.filter
import univention.admin.handlers
import univention.admin.localization

from univention.admin.handlers.container import default_container_for_objects

translation = univention.admin.localization.translation('univention.admin.handlers.container')
_ = translation.translate

module = 'container/ou'
operations = ['add', 'edit', 'remove', 'search', 'move', 'subtree_move']
childs = True
short_description = _('Container: Organisational Unit')
object_name = _('Organisational Unit')
object_name_plural = _('Organisational Units')
long_description = ''
options = {
	'default': univention.admin.option(
		short_description=short_description,
		default=True,
		objectClasses=['top', 'organizationalUnit']
	),
}
property_descriptions = {
	'name': univention.admin.property(
		short_description=_('Name'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		required=True,
		identifies=True,
		readonly_when_synced=True,
	),
	'policyPath': univention.admin.property(
		short_description=_('Add to standard policy containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'dhcpPath': univention.admin.property(
		short_description=_('Add to standard DHCP containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'dnsPath': univention.admin.property(
		short_description=_('Add to standard DNS containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'userPath': univention.admin.property(
		short_description=_('Add to standard user containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'groupPath': univention.admin.property(
		short_description=_('Add to standard group containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'computerPath': univention.admin.property(
		short_description=_('Add to standard computer containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'domaincontrollerPath': univention.admin.property(
		short_description=_('Add to standard Directory Node computer containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'networkPath': univention.admin.property(
		short_description=_('Add to standard network containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'sharePath': univention.admin.property(
		short_description=_('Add to standard share containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'printerPath': univention.admin.property(
		short_description=_('Add to standard printer containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'mailPath': univention.admin.property(
		short_description=_('Add to standard mail containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'licensePath': univention.admin.property(
		short_description=_('Add to standard license containers'),
		long_description='',
		syntax=univention.admin.syntax.boolean,
		size='One',
	),
	'description': univention.admin.property(
		short_description=_('Description'),
		long_description='',
		syntax=univention.admin.syntax.string,
		include_in_default_search=True,
		readonly_when_synced=True,
	),
}

layout = [
	Tab(_('General'), _('Basic settings'), layout=[
		Group(_('Organisational unit description'), layout=[
			["name", "description"],
		]),
		Group(_('Container settings'), _('Default position when adding objects'), layout=[
			["userPath", "groupPath"],
			["computerPath", "domaincontrollerPath"],
			["dnsPath", "dhcpPath"],
			["networkPath", "sharePath"],
			["printerPath", "mailPath"],
			["policyPath", "licensePath"],
		]),
	]),
]

mapping = univention.admin.mapping.mapping()
mapping.register('name', 'ou', None, univention.admin.mapping.ListToString)
mapping.register('description', 'description', None, univention.admin.mapping.ListToString)


class object(univention.admin.handlers.simpleLdap):
	module = module

	PATH_KEYS = {
		'userPath': 'univentionUsersObject',
		'groupPath': 'univentionGroupsObject',
		'computerPath': 'univentionComputersObject',
		'domaincontrollerPath': 'univentionDomainControllerComputersObject',
		'policyPath': 'univentionPolicyObject',
		'dnsPath': 'univentionDnsObject',
		'dhcpPath': 'univentionDhcpObject',
		'networkPath': 'univentionNetworksObject',
		'sharePath': 'univentionSharesObject',
		'printerPath': 'univentionPrintersObject',
		'mailPath': 'univentionMailObject',
		'licensePath': 'univentionLicenseObject',
	}

	def open(self):
		univention.admin.handlers.simpleLdap.open(self)

		pathResult, self.default_dn = default_container_for_objects(self.lo, self.position.getDomain())

		for prop in self.PATH_KEYS:
			self.info[prop] = '0'

		dn_bytes = self.dn.encode('UTF-8')
		for prop, attr in self.PATH_KEYS.items():
			if any(x == dn_bytes for x in pathResult.get(attr, [])):
				self.info[prop] = '1'

		self.save()

	def _ldap_pre_create(self):
		super(object, self)._ldap_pre_create()
		if configRegistry.is_false('directory/manager/child/cn/ou', True):
			if not self.lo.compare_dn(self.position.getDn(), configRegistry.get('ldap/base')):
				# it is possible to have a basedn with cn=foo
				# in this case it is allowed to create a ou
				# under a cn.
				if any(m and m.module == 'container/cn' for m in univention.admin.modules.identify(self.position.getDn(), self.lo.get(self.position.getDn()))):
					raise univention.admin.uexceptions.invalidChild(_('It is not allowed to create a container/ou as child object of a container/cn.'))

	def _ldap_post_create(self):
		super(object, self)._ldap_post_create()
		changes = []

		dn_bytes = self.dn.encode('UTF-8')
		for (prop, attr) in self.PATH_KEYS.items():
			if self.oldinfo.get(prop) != self.info.get(prop):
				entries = self.lo.getAttr(self.default_dn, attr)
				if self.info[prop] == '0':
					if dn_bytes in entries:
						changes.append((attr, self.dn.encode('utf-8'), b''))
				else:
					if dn_bytes not in entries:
						changes.append((attr, b'', self.dn.encode('utf-8')))

		if changes:
			self.lo.modify(self.default_dn, changes)

	def _ldap_pre_rename(self, newdn):
		super(object, self)._ldap_pre_rename(newdn)
		self.move(newdn)

	def _ldap_post_move(self, olddn):
		super(object, self)._ldap_post_move(olddn)
		settings_module = univention.admin.modules.get('settings/directory')
		settings_object = univention.admin.objects.get(settings_module, None, self.lo, position='', dn=self.default_dn)
		settings_object.open()
		for attr in ['dns', 'license', 'computers', 'shares', 'groups', 'printers', 'policies', 'dhcp', 'networks', 'users', 'mail']:
			if olddn in settings_object[attr]:
				settings_object[attr].remove(olddn)
				settings_object[attr].append(self.dn)
		settings_object.modify()

	def _ldap_post_modify(self):
		super(object, self)._ldap_post_modify()
		changes = []

		dn_bytes = self.dn.encode('UTF-8')
		for prop, attr in self.PATH_KEYS.items():
			if self.oldinfo.get(prop) != self.info.get(prop):
				if self.info[prop] == '0':
					changes.append((attr, dn_bytes, b''))
				else:
					changes.append((attr, b'', dn_bytes))
		if changes:
			self.lo.modify(self.default_dn, changes)

	def _ldap_pre_remove(self):
		super(object, self)._ldap_pre_remove()
		changes = []

		self.open()

		dn_bytes = self.dn.encode('UTF-8')
		for prop, attr in self.PATH_KEYS.items():
			if self.oldinfo.get(prop) == '1':
				changes.append((attr, dn_bytes, b''))
		self.lo.modify(self.default_dn, changes)

	@classmethod
	def unmapped_lookup_filter(cls):
		return univention.admin.filter.conjunction('&', [
			univention.admin.filter.expression('objectClass', 'organizationalUnit'),
			univention.admin.filter.conjunction('!', [univention.admin.filter.expression('objectClass', 'univentionBase')])
		])


lookup = object.lookup
lookup_filter = object.lookup_filter


def identify(dn, attr, canonical=False):
	return b'organizationalUnit' in attr.get('objectClass', []) and b'univentionBase' not in attr.get('objectClass', [])
