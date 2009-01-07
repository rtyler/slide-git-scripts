'''
	This post-commit hook is intended to be used to send "GITCOMMIT" emails to 
	the specified target address.

	The mails sent to the specified address look something like this

		From: 	tyler@slide.com
		To:		commits@slide.com
		Subject: 	GITCOMMIT [$MACHINE/$BRANCH/ce0520c] Minor change 

			Author: R. Tyler Ballance <tyler@slide.com>
			Commit: asdb123b123bfd123

			Changes committed:
				M	file

				Minor change

			diff --git a/file b/file
			index bc1f44a..4468922 100644
			--- a/file
			+++ b/file
			@@ -992,28 +992,5 @@ 

				$DIFF
	
	The post-commit hook also supports sending "attention" mails with the
	syntax of "attn tyler,jason". This will send a "[Review Request] mail
	formatted similar to the following:

		From: tyler@slide.com
		CC: tyler@slide.com, jason@slide.com
		Subject: [Review Request] Minor change

			(commit body here)
			--
			file |    6 ++++--
			1 files changed, 4 insertions(+), 2 deletions(-)

			diff --git a/file b/file
			index bc1f44a..4468922 100644
			--- a/file
			+++ b/file
			@@ -992,28 +992,5 @@ 

				$DIFF
'''

import getpass
import os
import socket
import smtplib
import sys

from optparse import OptionParser

SMTP_SERVER = 'smtp.your.com'
MAIL_SUFFIX = '@your.com'

def find_attn(commit):
	rc = re.findall(r'(?:^|\s)attn[:\s]+([\w \t,-]+[\w,])', commit)
	if not rc:
		return []
	if len(rc) > 1:
		return rc
	return rc[0].split(',')

def mail_commit(address):
	user = os.getenv('PG_USER') or getpass.getuser()
	machine = socket.gethostname()
	branch = os.popen('git symbolic-ref HEAD').read().rstrip()
	branch = branch.replace('refs/heads/', '')
	changes = os.popen('git diff HEAD^...HEAD --name-status --no-color').read().rstrip()
	message = os.popen('git show HEAD --pretty=format:"From: %(user)s@slide.com\r\nTo: %(to)s\r\nSubject: GITCOMMIT [%(hostname)s/%(branch)s/%%h] %%s\r\n\r\nAuthor: %%aN <%%ae>\r\nCommit: %%H\r\n\r\nChanges committed:\r\n\t%(changes)s\r\n\r\n%%s\r\n\r\n%%b\r\n\r\n" --no-color' % {
					'user' : user, 'to' : address, 'branch' : branch, 'hostname' : machine, 'changes' : '\n\t'.join(changes.split('\n'))}).read().rstrip()
	print 'Sending a commit mail to %s' % (address)

	s = smtplib.SMTP(SMTP_SERVER)
	addresses = [address]
	s.sendmail('%s@%s' % (user, MAIL_SUFFIX), addresses, message)

	addresses = find_attn(message)
	if addresses:
		addresses.append(user)
		addresses = ['%s@%s' % (a.strip(), MAIL_SUFFIX) for a in addresses]
		print 'Sending a review mail to: %s' % ','.join(addresses)
		message = os.popen('git format-patch --stdout HEAD^ --subject-prefix="Review Request" --cc=%s' % ','.join(addresses)).read().rstrip()
		s.sendmail('%s@%s' % (user, MAIL_SUFFIX) , addresses, message)
	s.quit()

if __name__ == '__main__':
	op = OptionParser()
	op.add_option('-m', '--mail', dest='address', help='Email address to mail commit messages to')
	opts, args = op.parse_args()

	if not opts.address:
		print '*** You need to specify a mailing address! ***'
		exit

	mail_commit(opts.address)

