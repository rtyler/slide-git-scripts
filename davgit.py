#!/usr/local/bin/python

import getpass
import os
import readline
import sys

USAGE = '''   usage: davgit.py [push/pull]
'''

NET_RC = '''
	machine your.webdav.server.with.auth
	login USER_LOGIN
	password USER_PASSWORD
'''
ENV_PASS_KEY = 'GIT_WEBDAV_SIGNED_PASSWORD'


def main():
	if not len(sys.argv) > 1:
		print USAGE
		return
	try:
		os.environ['GIT_SSL_NO_VERIFY'] = '1'
		user = getpass.getuser()
		password = os.getenv(ENV_PASS_KEY)
		if not password:
			password = getpass.getpass('LDAP Password: ')
		# Generate the ~/.netrc file that git-over-https needs to properly pass authentication via libcurl
		netrc = os.open(os.path.expanduser('~/.netrc'), os.O_CREAT | os.O_WRONLY)
		os.write(netrc, NET_RC.replace('USER_LOGIN', user).replace('USER_PASSWORD', password))
		os.close(netrc)

		# Needed to properly pass on extra args to `git pull` like:
		# `davgit.py pull origin master` -> `git pull origin master`
		os.system('git %s' % ' '.join(sys.argv[1:]))
	finally:
		os.remove(os.path.expanduser('~/.netrc'))


if __name__ == '__main__':
	main()
