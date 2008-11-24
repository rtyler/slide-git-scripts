'''
Copyright (c) 2008 Slide, Inc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

'''
	For questions, patches, etc contact R. Tyler Ballance <tyler@slide.com>
'''
import getpass
import os
import re
import socket
import smtplib
import sys
import time
import xmlrpclib

from optparse import OptionParser

def rpcProxy(user='qatracbot', password=None):
	password = password or os.getenv('TRAC_PASS')
	return xmlrpclib.ServerProxy('https://%s:%s@trac.slide.com/projects/Slide/login/xmlrpc' % (user, password))

def _send_commit_mail(user, address, subject, branch, commits, files, diff):
	print 'Sending a GITRECEIVE mail to %s' % address
	message = 'Commits pushed to %s:\n--------------------------------------\n\n%s\n--------------------------------------\n%s\n--------------------------------------\n%s' % (branch, commits, files, diff)
	_send_mail(user, address, subject, message)
def _send_attn_mail(user, destuser, diff):
	print 'Sending a "please review" mail to %s' % destuser
	message = '''Good day my most generous colleague! I would hold you in the highest esteem and toast you over my finest wines if you would kindly review this for me\n\n\t - %(user)s\n\nDiff:\n------------------------------------------------\n%(diff)s''' % {'diff' : diff, 'user' : user}
	addresses = []
	for d in destuser.split(','):
		addresses.append('%s@slide.com' % d)
	_send_mail(user, addresses, 'Please review this change', message)

def _send_mail(user, address, subject, contents):
	try:
		if not isinstance(address, list):
			address = [address]
		s = smtplib.SMTP('smtp.slide.com')
		message = 'From: %s@slide.com\r\nTo: %s\r\nSubject: %s\r\n\r\n%s\n' % (user, ', '.join(address), subject, contents)
		s.sendmail('%s@slide.com' % user, address, message)
		s.quit()
	except:
		print 'Failed to send the email :('

def _update_ticket(ticket, message, options={}):
	rpc = rpcProxy()
	rpc.ticket.update(ticket, message, options)
	return rpc

def find_re(commit):
	return map(int, re.findall(r'(?i)\s+re\s*#([0-9]+)', commit))
def handle_re(branch, commit, ticket):
	print 'Annotating ticket #%s' % ticket
	message = '''The following was committed in "%(branch)s":
			{{{	
%(commit)s }}}
		''' % {'branch' : branch, 'commit' : commit}
	_update_ticket(ticket, message)

def find_qa(commit):
	return map(int, re.findall(r'(?i)\s+qa\s*#([0-9]+)', commit))
def handle_qa(branch, commit, ticket):
	print 'Marking ticket #%s as "ready for QA"' % ticket
	message = '''The following was committed in "%(branch)s":
			{{{	
%(commit)s }}}
		''' % {'branch' : branch, 'commit' : commit}
	rpc = _update_ticket(ticket, message, options={'status' : 'qa'})

def find_attn(commit):
	return re.findall(r'(?i)\s+attn\s*([A-Za-z,]+)', commit)
def handle_attn(branch, commit, attn):
	# Unpack commit from this: "commit 5f4c31f3c31347c62d68ecb5f2c9afa3333f4ad0\nAuthor: R. Tyler Ballance <tyler@ccnet.dev.slide.com>\nDate: Wed Nov 12 16:57:32 2008 -0800 \n\n Merge commit 'git-svn' \n\n  \n \n"
	try:
		commit_hash = commit.split('\n')[0].split(' ')[1]
	except:
		return # fuk it
	diff = os.popen('git show --no-color %s --pretty=format:"Author: %%cn <%%ce>%%n%%s%%n%%n%%b%%n%%n%%H"' % commit_hash).read().rstrip()
	_send_attn_mail(getpass.getuser(), attn,  diff)

def mail_push(address, oldrev, newrev, refname):
	user = getpass.getuser()
	machine = socket.gethostname()
	base_git_diff = 'git diff %s %s' % (oldrev, newrev)
	files_diffed = os.popen('%s --name-status' % (base_git_diff)).read().rstrip()
	full_diff = os.popen('%s -p --no-color' % (base_git_diff)).read().rstrip()
	''' git rev-parse --not --branches | grep -v "$new" | git rev-list "$old".."$new" --stdin '''
	commits = os.popen('git rev-parse --not --branches | grep -v "%s" | git rev-list %s..%s --stdin --pretty=format:"Author: %%cn <%%ce>%%nDate: %%cd %%n%%n %%s %%n%%n %%b %%n %%n-------[post-receive marker]------%%n" --first-parent ' % (newrev, oldrev, newrev)).read().rstrip()
	branch = refname.split('/')[-1]
	mail_subject = 'GITRECEIVE [%s/%s] %s files changed' % (machine, branch, len(files_diffed.split('\n')))

	if branch == 'master':
		print 'Executing the Git-to-Subversion job!'
		os.system('/usr/bin/env wget -q -O /dev/null http://hudson.corp.slide.com/job/Git-to-Subversion/build')
	if branch == 'master-release':
		print 'Tagging release branch'
		tagname = 'livepush_%s' % (time.strftime('%Y%m%d%H%M%S', time.localtime()))
		sys.stderr.write('Creating a tag named: %s\n\n' % tagname)
		os.system('git tag %s' % tagname)
		mail_subject = '%s (tagged: %s)' % (mail_subject, tagname)
	print 'Queuing the Hudson job for "%s"' % branch
	os.system('/usr/bin/env wget -q -O /dev/null http://hudson.corp.slide.com/job/%s/build' % branch)

	_send_commit_mail(user, address, mail_subject, branch, commits, files_diffed, full_diff)

	if branch == 'master':
		return # we don't want to update tickets and such for master/merges

	commits = filter(lambda c: len(c), commits.split('-------[post-receive marker]------'))
	commits.reverse()
	for c in commits:
		if c.find('Squashed commit') >= 0:
			continue # Skip bullsiht squashed commit

		for attn in find_attn(c):
			handle_attn(branch, c, attn)

		for ticket in find_re(c):
			handle_re(branch, c, ticket)

		for ticket in find_qa(c):
			handle_qa(branch, c, ticket)


if __name__ == '__main__':
	op = OptionParser()
	op.add_option('-m', '--mail', dest='address', help='Email address to mail git push messages to')
	op.add_option('-o', '--oldrev', dest='oldrev', help='Old revision we\'re pushing from')
	op.add_option('-n', '--newrev', dest='newrev', help='New revision we\'re pushing to')
	op.add_option('-r','--ref', dest='ref', help='Refname that we\'re pushing')
	opts, args = op.parse_args()

	if not opts.address or not opts.oldrev or not opts.newrev or not opts.ref:
		print '*** You left out some needed parameters! ***'
		exit

	mail_push(opts.address, opts.oldrev, opts.newrev, opts.ref)


