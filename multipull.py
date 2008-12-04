#!/usr/local/bin/python

import optparse
import os

if __name__ == '__main__':
	op = optparse.OptionParser()
	op.add_option('-r', '--repos', dest='repos', help='Specify the repositories to pull from ( repo1,repo2,repo3 )')
	op.add_option('-b', '--branch', dest='branch', help='Specify the branch to pull from the respective repositories')

	opts, args = op.parse_args()
	
	if not opts.repos or not opts.branch:
		print '  *** Incomplete parameters ***'
		print
		print '  Please run this script with -h, and use the appropriate options'
		exit

	repos = opts.repos.split(',')
	repos = map(lambda r: r.strip(), repos)
	branch = opts.branch.strip()

	rc = os.system('git checkout %s' % (branch))
	repos.reverse()
	while rc == 0 and len(repos):
		repo = repos.pop()
		print 'Pulling from %s:%s' % (repo, branch)
		rc = os.system('git pull %s %s' % (repo, branch))
	if rc:
		print 'Crap! Some sort failure occurred, resolve and rerun :)'
		exit
	print 'YAY! All done'	



