#!/usr/intel/bin/python2.7 -B

import os
import sys
import argparse
import getpass
import string
import re
from datetime import datetime

sys.path.append(os.path.abspath("{}/../..".format(os.path.dirname(__file__))))
from tools.libs.helper_lib import *


class PacmanRootRelease:

    def __init__(self):

        self.version = ""
        self.train = ""

        # Check the current user to make sure this is being run under presi_super_user or drv_<train> account
        if getpass.getuser() != "presi_super_user" and "drv_" not in getpass.getuser():
            print_error("######################################################################\n\nError: You must be logged as drv_<train> faceless account to use this automation. Pacman hotfix will be released to /p/hdk/cad/pacman/<train> area depending on drv_<train> faceless account being used.\nPlease MAKE SURE that you are using the correct account for release!!!\n\n##########################################################################")

        if "drv_" in getpass.getuser():
            self.train = getpass.getuser()[4].upper() + getpass.getuser()[5:]

        parser = argparse.ArgumentParser(description='This script releases a Pacman root and syncs it across all geos')
        if getpass.getuser() == "presi_super_user":
            parser.add_argument('-action', '--action', help='Please specify action to perform.', choices=["release", "replace", "delete", "addAccess", "getAccess", "rmAccess"], required=True)
            parser.add_argument('-t', '--train', help='Please provide train name to be released to for hotfix release.', choices=["Arenal", "Bullet", "Cascade", "Echo", "Julio", "Light", "Longhorn", "Lunas", "Paddington", "Rave", "Setanta"], required=True)
            parser.add_argument('-m', '--maintainer', help='Please provide IDSID for member(s) to be added/removed as maintainers for hotfix release.')
        else:
            parser.add_argument('-action', '--action', help='Please specify action to perform.', choices=["release", "replace", "delete"], required=True)
        parser.add_argument('-p', '--product', help='Please provide product name, for example snr for this hotfix release.')
        parser.add_argument('-s', '--stepping', help='Please provide product stepping, for example a0 for this hotfix release.')
        parser.add_argument('-src', '--source_dir', help='Please provide source dir which will be released to /p/hdk/cad/pacman/<train> area.')
        parser.add_argument('-v', '--version', help='Please provide version name to be replaced/deleted in /p/hdk/cad/pacman/<train> area.')

        self.args = parser.parse_args()

        if self.train == "":
            self.train = self.args.train

        if self.args.action == "release":
            if not (self.args.product and self.args.stepping and self.args.source_dir):
                print_error("Please specify -p, -s and -src switches for hotfix release.")
        elif self.args.action == "replace":
            if not (self.args.source_dir and self.args.version):
                print_error("Please provide new source_dir and existing version name to be replaced by using -src and -v switches.")
        elif self.args.action == "delete":
            if not self.args.version:
                print_error("Please provide version name to be deleted in /p/hdk/cad/pacman/" + self.train + " area by using -v switch.")
        elif self.args.action == "addAccess" or self.args.action == "rmAccess":
            if not self.args.maintainer:
                print_error("Please provide IDSID for member(s) to be added/removed as maintainers for hotfix release by using -m switch, for example -m user1,user2,...")

        if self.args.action == "release" or self.args.action == "replace":
            if not os.path.exists(os.path.realpath(self.args.source_dir)):
                print_error("The source dir specified by -src switch is not exist! Please input valid source dir for release.")
        if self.args.action == "replace" or self.args.action == "delete":
            if not os.path.exists("/p/hdk/cad/pacman/" + self.train + "/" + self.args.version):
                print_error("The version name specified by -v switch is not exist in /p/hdk/cad/pacman/" + self.train + " area.")

    def run(self):
        os.environ['CRT_DIR'] = "/nfs/site/disks/crt_linktree_1/crt/latest"

        if self.args.action == "release":
            print_info("Pacman hotfix will be releasing to the following path: /p/hdk/cad/pacman/{}/ ...".format(self.train))
            now = datetime.now()
            date = now.strftime("%m%d%Y")
            if os.path.isfile(self.args.source_dir + "/.git/config"):
                f = open(self.args.source_dir + "/.git/config", "r")
            else:
                f = open(self.args.source_dir + "/.git_bk/config", "r")
            for x in f:
                if x.find("29418") != -1:
                    searchObj = re.search(r'url = ssh://git@gitlab.devtools.intel.com:29418/core_fork_group/(.*)/pacman_core.git', x)
                    self.version = "pacman_core_" + searchObj.group(1) + "_" + date
                    break

            flag = 0
            for suffix in string.ascii_lowercase:
                if not os.path.exists("/p/hdk/cad/pacman/" + self.train + "/" + self.version + suffix + "_" + self.args.product + "_" + self.args.stepping):
                    self.version = self.version + suffix + "_" + self.args.product + "_" + self.args.stepping
                    flag = 1
                    break

            if flag == 0:
                print_error("You have exceeded the maximum number of releases (26) per day.")

            if os.path.isfile(self.args.source_dir + "/.git/config"):
                run_cmd("mv {}/.git {}/.git_bk".format(self.args.source_dir, self.args.source_dir))

            run_cmd("$CRT_DIR/client/crt install -tool pacman/{} -type cheetah_cad -version {} -src {}".format(self.train, self.version, self.args.source_dir))
            run_cmd("mv {}/.git_bk {}/.git".format(self.args.source_dir, self.args.source_dir))
            print_info("Pacman Root Release Path: /p/hdk/cad/pacman/{}/{}".format(self.train, self.version))

        if self.args.action == "replace":
            if os.path.isfile(self.args.source_dir + "/.git/config"):
                run_cmd("mv {}/.git {}/.git_bk".format(self.args.source_dir, self.args.source_dir))

            run_cmd("$CRT_DIR/client/crt install -tool pacman/{} -type cheetah_cad -version {} -src {} -replace".format(self.train, self.args.version, self.args.source_dir))
            run_cmd("mv {}/.git_bk {}/.git".format(self.args.source_dir, self.args.source_dir))

        if self.args.action == "delete":
            run_cmd("$CRT_DIR/client/crt rmVersion -tool pacman/{} -type cheetah_cad -version {}".format(self.train, self.args.version))

        if self.args.action == "addAccess":
            run_cmd("$CRT_DIR/client/crt addAccess -tool pacman/{} -type cheetah_cad -maintainer {}".format(self.train, self.args.maintainer))

        if self.args.action == "getAccess":
            run_cmd("$CRT_DIR/client/crt getAccess -tool pacman/{} -type cheetah_cad".format(self.train))

        if self.args.action == "rmAccess":
            run_cmd("$CRT_DIR/client/crt rmAccess -tool pacman/{} -type cheetah_cad -maintainer {}".format(self.train, self.args.maintainer))


if __name__ == "__main__":
    prr = PacmanRootRelease()
    prr.run()
