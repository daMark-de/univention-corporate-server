#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  authentication mechanisms
#
# Copyright 2014-2021 Univention GmbH
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

from __future__ import absolute_import

import traceback

import ldap
from ldap.filter import filter_format

import notifier
import notifier.signals as signals
import notifier.threads as threads

import univention.admin.uexceptions as udm_errors
from univention.lib.i18n import Locale

from univention.management.console.log import AUTH
from univention.management.console.config import ucr
from univention.management.console.ldap import get_machine_connection, reset_cache
from univention.management.console.pam import PamAuth, AuthenticationError, AuthenticationFailed, AuthenticationInformationMissing, PasswordExpired, AccountExpired, PasswordChangeFailed

try:
	from typing import Any, Dict, Optional, Tuple, Union  # noqa F401
	from univention.management.console.protocol.meesage import Request  # noqa F401
except ImportError:
	pass


class AuthenticationResult(object):

	def __init__(self, result, locale):  # type: (Union[BaseException, Dict[str, str]], Optional[str]) -> None
		from univention.management.console.protocol.definitions import SUCCESS, BAD_REQUEST_UNAUTH
		self.credentials = None
		self.status = SUCCESS
		self.authenticated = not isinstance(result, BaseException)
		if self.authenticated:
			self.credentials = result
		self.message = None
		self.result = None  # type: Optional[Dict[str, Any]]
		self.password_expired = False
		if isinstance(result, AuthenticationError):
			self.status = BAD_REQUEST_UNAUTH
			self.message = str(result)
			self.result = {}
			if isinstance(result, PasswordExpired):
				self.result['password_expired'] = True
			elif isinstance(result, AccountExpired):
				self.result['account_expired'] = True
			elif isinstance(result, AuthenticationInformationMissing):
				self.result['missing_prompts'] = result.missing_prompts
			elif isinstance(result, PasswordChangeFailed):
				self.result['password_change_failed'] = True
			if isinstance(result, (PasswordExpired, PasswordChangeFailed)):
				_locale = Locale(locale)
				self.message += (' %s' % (ucr.get('umc/login/password-complexity-message/%s' % (_locale.language,), ucr.get('umc/login/password-complexity-message/en', '')),)).rstrip()
		elif isinstance(result, BaseException):
			self.status = 500
			self.message = str(result)
		else:
			self.result = {'username': result['username']}

	def __bool__(self):  # type: () -> bool
		return self.authenticated

	__nonzero__ = __bool__  # Python 2


class AuthHandler(signals.Provider):

	def __init__(self):  # type: () -> None
		signals.Provider.__init__(self)
		self.signal_new('authenticated')

	def authenticate(self, msg):  # type: (Request) -> None
		# PAM MUST be initialized outside of a thread. Otherwise it segfaults e.g. with pam_saml.so.
		# See http://pam-python.sourceforge.net/doc/html/#bugs

		args = msg.body.copy()
		locale = args.pop('locale', None)
		args.pop('pam', None)
		args.setdefault('new_password', None)
		args.setdefault('username', '')
		args.setdefault('password', '')

		pam = PamAuth(locale)
		thread = threads.Simple('pam', notifier.Callback(self.__authenticate_thread, pam, **args), notifier.Callback(self.__authentication_result, pam, msg, locale))
		thread.run()

	def __authenticate_thread(self, pam, username, password, new_password, auth_type=None, **custom_prompts):  # type: (PamAuth, str, str, Optional[str], Optional[str], **Optional[str]) -> Tuple[str, str]
		AUTH.info('Trying to authenticate user %r (auth_type: %r)' % (username, auth_type))
		username = self.__canonicalize_username(username)
		try:
			pam.authenticate(username, password, **custom_prompts)
		except AuthenticationFailed as auth_failed:
			AUTH.error(str(auth_failed))
			raise
		except PasswordExpired as pass_expired:
			AUTH.info(str(pass_expired))
			if new_password is None:
				raise

			try:
				pam.change_password(username, password, new_password)
			except PasswordChangeFailed as change_failed:
				AUTH.error(str(change_failed))
				raise
			else:
				AUTH.info('Password change for %r was successful' % (username,))
				return (username, new_password)
		else:
			AUTH.info('Authentication for %r was successful' % (username,))
			return (username, password)

	def __canonicalize_username(self, username):  # type: (str) -> str
		try:
			lo, po = get_machine_connection(write=False)
			result = None
			if lo:
				attr = 'mailPrimaryAddress' if '@' in username else 'uid'
				result = lo.search(filter_format('(&(%s=%s)(objectClass=person))', (attr, username)), attr=['uid'], unique=True)
			if result and result[0][1].get('uid'):
				username = result[0][1]['uid'][0].decode('utf-8')
				AUTH.info('Canonicalized username: %r' % (username,))
		except (ldap.LDAPError, udm_errors.ldapError) as exc:
			# /etc/machine.secret missing or LDAP server not reachable
			AUTH.warn('Canonicalization of username was not possible: %s' % (exc,))
			reset_cache()
		except Exception:
			AUTH.error('Canonicalization of username failed: %s' % (traceback.format_exc(),))
		return username

	def __authentication_result(self, thread, result, pam, request, locale):  # type: (threads.Simple, Union[BaseException, Tuple[str, str], Dict[str, str]], PamAuth, Request, Optional[str]) -> None
		pam.end()
		if isinstance(result, BaseException) and not isinstance(result, (AuthenticationFailed, AuthenticationInformationMissing, PasswordExpired, PasswordChangeFailed, AccountExpired)):
			msg = ''.join(thread.trace + traceback.format_exception_only(*thread.exc_info[:2]))
			AUTH.error(msg)
		if isinstance(result, tuple):
			username, password = result
			result = {'username': username, 'password': password, 'auth_type': request.body.get('auth_type')}
		auth_result = AuthenticationResult(result, locale)
		self.signal_emit('authenticated', auth_result, request)
