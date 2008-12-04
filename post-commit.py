'''
	This post-commit hook is intended to be used to send "GITCOMMIT" emails to 
	the specified target address.

	The mails sent to the specified address look something like this

		From: 	tyler@slide.com
		To:		commits@slide.com
		Subject: 	GITCOMMIT [$MACHINE/$BRANCH] Minor change (ce0520c)

			commit ce0520ceebb756aee7fce58f4fd643a6bca349d8
			Author: R. Tyler Ballance <tyler@slide.com>
			Date:   Thu Dec 4 10:37:55 2008 -0800

				Minor change

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

def mail_commit(address):
	user = os.getenv('PG_USER') or getpass.getuser()
	machine = socket.gethostname()
	base_git_cmd = 'git log --max-count=1 --no-color --no-merges --author=%s' % (user)
	branch = os.popen('git branch --no-color | grep "* " | sed \'s/* //g\'').read().rstrip()
	commit_diff = os.popen('%s --unified=4 --pretty=medium' % base_git_cmd).read().rstrip()
	mail_subject = os.popen('%s --pretty=format:"%%s (%%h)"'  % (base_git_cmd)).read().rstrip()
	mail_subject = 'GITCOMMIT [%s/%s] %s' % (machine, branch, mail_subject)

	print 'Sending a commit mail to %s' % (address)

	s = smtplib.SMTP(SMTP_SERVER)
	sender = os.getenv('GIT_FROM') or ('%s%s' % (user, MAIL_SUFFIX))
	message = 'From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s' % (sender, address, mail_subject, commit_diff)
	s.sendmail('%s%s' % (user, MAIL_SUFFIX), [address], message)
	s.quit()

if __name__ == '__main__':
	op = OptionParser()
	op.add_option('-m', '--mail', dest='address', help='Email address to mail commit messages to')
	opts, args = op.parse_args()

	if not opts.address:
		print '*** You need to specify a mailing address! ***'
		exit

	mail_commit(opts.address)

