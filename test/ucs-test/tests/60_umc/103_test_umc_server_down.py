#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Test error messages if UMC server is down
## exposure: dangerous
## packages: [univention-management-console-server]

import json
import socket
import subprocess

import pytest

from univention.lib.umc import ConnectionError, ServiceUnavailable


class Test_ServerDown_Messages(object):

	def test_umc_webserver_down(self, Client):
		try:
			subprocess.call(['service', 'univention-management-console-web-server', 'stop'])
			with pytest.raises(ServiceUnavailable) as exc:
				Client().umc_get('modules')
			assert json.loads(exc.value.response.body)['message'] == 'The Univention Management Console Web Server could not be reached. Please restart univention-management-console-web-server or try again later.'
			assert exc.value.response.reason == 'UMC-Web-Server Unavailable'
		finally:
			subprocess.call(['service', 'univention-management-console-web-server', 'start'])

	def test_umc_server_down(self, Client):
		try:
			subprocess.call(['service', 'univention-management-console-server', 'stop'])
			with pytest.raises(ServiceUnavailable) as exc:
				Client().umc_get('modules')
			assert exc.value.response.reason == 'UMC Service Unavailable'
			assert exc.value.message.splitlines() == [
				'The Univention Management Console Server is currently not running. ',
				'If you have root permissions on the system you can restart it by executing the following command:',
				' * service univention-management-console-server restart',
				'The following logfile may contain information why the server is not running:',
				' * /var/log/univention/management-console-server.log',
				'Otherwise please contact an administrator or try again later.',
			]
		finally:
			subprocess.call(['service', 'univention-management-console-server', 'start'])

	def test_apache_down(self, Client):
		try:
			subprocess.call(['service', 'apache2', 'stop'])
			with pytest.raises(ConnectionError) as exc:
				Client().umc_get('modules')
			assert isinstance(exc.value.reason, socket.error)
		finally:
			subprocess.call(['service', 'apache2', 'start'])
