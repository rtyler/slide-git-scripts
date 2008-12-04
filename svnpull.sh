#!/bin/bash

MERGE_BRANCH=mergemaster
REPO=$1
BRANCH=$2

if [[ -z "${1}" || -z "${2}" ]]; then
	echo "===> You must provide a \"remote\" and a \"refspec\" for Git to use!"
	echo "===> Exiting :("
	exit 1;
fi

LATEST_COMMIT=`git log --max-count=1 --no-merges --pretty=format:"%H"`

function master
{
	echo "==> Making sure we're on 'master'"
	git checkout master
}

function setup_mergemaster 
{
	master
	echo "==> Killing the old mergemaster branch"
	git branch -D $MERGE_BRANCH

	echo "==> Creating a new mergemaster branch"
	git checkout -b $MERGE_BRANCH
	git checkout master
}

function cleanup
{
	rm -f .git/SVNPULL_MSG
}

function prepare_message
{
	master

	echo "===> Pulling from ${REPO}:${BRANCH}"
	git pull ${REPO} ${BRANCH}
	git checkout ${MERGE_BRANCH}

	echo "==> Merging across change from master to ${MERGE_BRANCH}"
	git pull --no-commit --squash . master

	cp .git/SQUASH_MSG .git/SVNPULL_MSG

	master
}

function merge_to_svn
{
	git reset --hard ${LATEST_COMMIT}
	master
	setup_mergemaster

	echo "===> Pulling from ${REPO}:${BRANCH}"
	git pull ${REPO} ${BRANCH}
	git checkout ${MERGE_BRANCH}

	echo "==> Merging across change from master to ${MERGE_BRANCH}"
	git pull --no-commit --squash . master

	echo "==> Committing..."
	git commit -a -F .git/SVNPULL_MSG && git-svn dcommit --no-rebase

	cleanup
}

setup_mergemaster

prepare_message

merge_to_svn

master

echo "===> All done!"

