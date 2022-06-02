#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B


import os
import sys
import os.path
import argparse
import tempfile
import getpass
import string
import re

sys.path.append(os.path.abspath("{}/../..".format(os.path.dirname(__file__))))
from tools.libs.helper_lib import *


class PacmanRootRelease:
    release_path = "/p/pde/htd/Site/Infra/GlobalTools/pacman_root"

    def __init__(self):

        self.all_sites = {
            "pdx": "Oregon - Jones Farm",
            "fm": "Folsom",
            "iil": "IDC",
            "sc": "Santa Clara",
            "png": "Penang"}

        parser = argparse.ArgumentParser(description='This script releases a pacman root and syncs it across all geos')
        parser.add_argument('-t', '--test', help='Put into test mode', action="store_true")
        self.args = parser.parse_args()

        # Check the current user to make sure this is being run under presi_super_user 
        if getpass.getuser() != "presi_super_user":
            print_error("This script must run under presi_super_user not user '{}'".format(getpass.getuser()))

        self.home_dir = os.path.expanduser('~')

        # Create a temp dir
        self.tmp_path_central = tempfile.mkdtemp()
        self.tmp_path_teamforge = tempfile.mkdtemp()
        run_cmd("chmod g+rx %s" % self.tmp_path_central) #Temp dir is user only by default
        run_cmd("chmod g+rx %s" % self.tmp_path_teamforge) #Temp dir is user only by default

    def run(self):
        self.generate_name()
        self.confirm_sites()
        self.run_ctci_cmd()
        # stang25: Release to old release path (/p/pde/htd/Site/Infra/GlobalTools/pacman_root) as well for now
        #self.check_and_sync()
        # stang25: End
        print_info("Pacman core code release process executed successfully. Diff_report generated at %s/diff_report_gitlab_vs_teamforge.txt" % self.home_dir)

    def generate_name(self):
        workweek = run_cmd("workweek -f '%yww%02IW'", return_data=1).rstrip()

        # Make sure to use the main git, not whatver may be overrided by source projects
        run_cmd("/usr/intel/bin/git clone ssh://git@gitlab.devtools.intel.com:29418/tvpv-my/pacman_core.git %s " % self.tmp_path_central)
        run_cmd("/usr/intel/bin/git clone ssh://git-amr-7.devtools.intel.com:29418/mdo_cgf-pacman_core_code %s " % self.tmp_path_teamforge)
        os.chdir(self.tmp_path_central)
        run_cmd("find . -type f -exec md5sum {} + | sort -k 2 > %s/dir_gitlab.txt" % self.home_dir)

        # run_cmd("/usr/intel/bin/git checkout master")

        tags = run_cmd("/usr/intel/bin/git tag", return_data=1).splitlines()

        workweek = run_cmd("workweek -f '%yww%02IW'", return_data=1).rstrip()

        tag_prefix = "pacman_core_v{0}".format(workweek.decode())
        if self.args.test:
            tag_prefix = "TESTING_" + tag_prefix

        # Check for unique tag. Git errors if it already exists
        for suffix in string.ascii_lowercase:
            if tag_prefix + suffix not in tags:
                release_name = tag_prefix + suffix
                break
        
        os.chdir(self.tmp_path_teamforge)
        
        run_cmd("mv .git {}/.git_bk".format(self.home_dir))
        run_cmd("cp -r %s/.git ." % self.tmp_path_central)
        run_cmd("/usr/intel/bin/git add --all")
        run_cmd("/usr/intel/bin/git checkout --force")
        run_cmd("/usr/intel/bin/git pull")
        run_cmd("rm -rf .git")
        run_cmd("mv {}/.git_bk .git".format(self.home_dir))
        run_cmd("/usr/intel/bin/git add --all")
        run_cmd("find . -type f -exec md5sum {} + | sort -k 2 > %s/dir_teamforge.txt" % self.home_dir)
        run_cmd("diff -u {0}/dir_gitlab.txt {1}/dir_teamforge.txt > {2}/diff_report_gitlab_vs_teamforge.txt || true".format(self.home_dir, self.home_dir, self.home_dir))
        diff_list = []
        f = open(self.home_dir + "/diff_report_gitlab_vs_teamforge.txt", "r")
        for line in f:
            if re.search("^[-+]\w", line) is not None:
                if re.search("\s\s\.\/\.git.+", line) is not None:
                    continue
                else:
                    diff_list.append(line)
        if len(diff_list) > 0:
            diff_str = " ".join(diff_list)
            print_error("There are mismatched files between Gitlab and Teamforge repo, please check diff_report from {}/diff_report_gitlab_vs_teamforge.txt for more info. \n\nMismatched files: \n {}".format(self.home_dir, diff_str))
        run_cmd("git commit -m 'commit new changes from GitLab during core code release process with tag %s'" % release_name)
        run_cmd("/usr/intel/bin/git push")

        os.chdir(self.tmp_path_central)
        run_cmd("/usr/intel/bin/git tag %s -m 'Pacman Root Release'" % release_name)
        run_cmd("/usr/intel/bin/git push origin %s" % release_name)

        print_info("Pacman Root Release Name: {}".format(release_name))
        self.rel_name = release_name

        '''# stang25: Keep this when CRT is up
        # Make sure to use the main git, not whatver may be overrided by source projects
        run_cmd("/usr/intel/bin/git clone ssh://git-amr-7.devtools.intel.com:29418/mdo_cgf-pacman_core_code %s " % self.tmp_path_teamforge)
        os.chdir(self.tmp_path)

        # run_cmd("/usr/intel/bin/git checkout master")

        tags = run_cmd("/usr/intel/bin/git tag", return_data=1).splitlines()

        workweek = run_cmd("workweek -f '%yww%02IW'", return_data=1).rstrip()

        tag_prefix = "pacman_core_v{0}".format(workweek)
        if self.args.test:
            tag_prefix = "TESTING_" + tag_prefix

        #Check for unique tag. Git errors if it already exists
        for suffix in string.ascii_lowercase:
            if tag_prefix + suffix not in tags:
                release_name = tag_prefix + suffix
                break

        # stang25: Commented out as these steps are covered in ctci_cmd 
        #run_cmd("/usr/intel/bin/git tag %s -m 'Pacman Root Release'" % release_name)
        #run_cmd("/usr/intel/bin/git push origin %s" % release_name)

        # Remove .git directory
        #run_cmd("rm -rf .git")

        # Change Group and Permissions
        #run_cmd("chgrp gdlusers -R %s" % self.tmp_path)
        #run_cmd("chmod 550 -R %s" % self.tmp_path)

        print_info("Pacman Root Release Name: {}".format(release_name))
        self.rel_name = release_name'''

    def confirm_sites(self):
        pass

    def check_for_existing_release(self, rsync_srvr):
        '''

        :param rsync_srvr:
        :return: True if existing release is found with the same name, else return False
        :rtype: bool
        '''
        # Make sure the path exists
        if run_cmd("ssh {0} 'ls {1}'".format(rsync_srvr, PacmanRootRelease.release_path), err_check=0) is None:
            run_cmd("ssh {0} 'mkdir -p {1}; chgrp -R gdlusers {1}; chmod -R g+rx "
                    "{1}'".format(rsync_srvr, PacmanRootRelease.release_path))

        # Check to make sure this release name doesn't already exist in this site
        if run_cmd("ssh {0} 'ls {1}/{2}'".format(rsync_srvr, PacmanRootRelease.release_path, self.rel_name),
                   err_check=0) is not None:
            return True

        return False

    def check_and_sync(self):
        # For each site, do the following:
        #   - Check that a release of this name doesn't already exist at that site
        #   - Sync release to the site
        
        os.chdir(self.tmp_path_teamforge)
        # Remove .git directory
        run_cmd("rm -rf .git")

        # Change Group and Permissions
        run_cmd("chgrp gdlusers -R %s" % self.tmp_path_teamforge)
        run_cmd("chmod 550 -R %s" % self.tmp_path_teamforge)

        for site in self.all_sites:
            rsync_srvr = "rsync.{}.intel.com".format(site)

            if self.check_for_existing_release(rsync_srvr):
                print_warning("Skipping {} because a release with this name already exists there".format(rsync_srvr))
                continue
            
            # Do the rsync
            print_info("Rsyncing to {}".format(rsync_srvr))
            run_cmd("rsync -avz {0}/ {1}:{2}/{3}".format(self.tmp_path_teamforge, rsync_srvr, PacmanRootRelease.release_path,
                                                         self.rel_name))

    def run_ctci_cmd(self):
        # Call ctci_cmd to check in and release Pacman core code to $RTL_PROJ_TOOLS/pacman at every sites       
        print_info("Running ctci_cmd to check in and release Pacman core code to $RTL_PROJ_TOOLS/pacman")  
        run_cmd("chgrp soc -R %s" % self.tmp_path_teamforge)
        run_cmd("chmod 770 -R %s" % self.tmp_path_teamforge)
        os.environ['PROJECT'] = 'hdk'
        run_cmd("/p/hdk/rtl/proj_tools/cadtools-ci/latest/cadtools_ci_client/ctci_cmd --action checkin -tool pacman -source {} -comment \"Release for {}\" -release -version {} -area proj_tools".format(self.tmp_path_teamforge, self.rel_name, self.rel_name))


if __name__ == "__main__":
    prr = PacmanRootRelease()
    prr.run()
