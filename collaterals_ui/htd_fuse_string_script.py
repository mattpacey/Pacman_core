#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B

#####################################################################################
# Author: Shirley Montealegre <smonteal>
# Date:   w39'17
#
# This script gets the fuse string recipe from the emu .mem generated files
#
# To run:
# > chmod u+x htd_fuse_string_script.py
# > htd_fuse_string_script.py -fusefiles <push_pop_emu_results_path_with_.mem> -last_rf_df <last_rf_data_for_direct_fuses> -fill_vf <value to use for virtual fuses>
# Ex.
# > htd_fuse_string_script.py -fusefiles /nfs/pdx/disks/mve_knh_013/users_eng/Run_emul_fuse_mem_dump/push_pop_ss.0 -last_rf_df 9 -fill_vf 1
#####################################################################################

import os
import sys
import re
import glob
import argparse
from subprocess import Popen, PIPE


def run_cmd(cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, error = proc.communicate()
    exitcode = proc.returncode
    return (exitcode, out.decode("utf-8"), error.decode("utf-8"))


def line_to_bin_32(line):
    line = "0x" + line
    line = (bin(int(line, 16))[2:]).zfill(32)
    return line


parser = argparse.ArgumentParser(description='Process args')

parser.add_argument(
    '-fusefiles', help='Path to the .mem fuse files', type=str, required=True)
parser.add_argument(
    '-last_rf_df', help='Last rf_data # for direct fuses', type=int, required=False)
parser.add_argument(
    '-fill_vf', help='Enable complete string with given virtual fuse value, ex. 1 or 0', type=int, required=False)
args = parser.parse_args()

#sysfuse_files_path = sys.argv[1]
sysfuse_files_path = args.fusefiles


cmd = "gunzip %s/*i_fuse_ram_wrapper*.gz" % sysfuse_files_path
(exit_code, fuse_list, error) = run_cmd(cmd)

# Get sysfuse files list
glob_cmd = "%s/*i_fuse_ram_wrapper*" % sysfuse_files_path
sysfuse_files = glob.glob(glob_cmd)
sysfuse_files.sort(key=lambda var: [int(x) if x.isdigit() else x for x in re.findall(r'[^0-9]|[0-9]+', var)])


if args.last_rf_df is not None:
    rf_data = args.last_rf_df
else:
    rf_data = len(sysfuse_files)

fuse_str = ""

# Concatenate all sysfuse file without header
with open("fuse_string.txt", "w") as fuse_string:
    count = 0
    for f in sysfuse_files:
        if count <= int(rf_data):
            count = count + 1
            with open(f, "r") as fuse_file:
                flag = 0
                for line in fuse_file:
                    if not line.strip().startswith("//"):
                        # Detect iteration in the .mem
                        if re.match("^@", line):
                            flag = 1
                            line = line.replace("@", "")
                            line = line.replace("\n", "")
                            (first_row, last_row) = re.split(r',|\+s', line)
                            first_row = "0x" + first_row
                            last_row = "0x" + last_row
                            iterations = int(last_row, 16) - int(first_row, 16) + 1

                        elif (flag == 1):
                            flag = 0
                            # Print fuse value for the specified times in .mem
                            for i in range(iterations):
                                fuse_val = line_to_bin_32(line)
                                fuse_str = fuse_val + fuse_str

                        else:
                            fuse_val = line_to_bin_32(line)
                            fuse_str = fuse_val + fuse_str
        else:
            # Complete fuse string to 147456 size using the receive value
            if args.fill_vf is not None:
                if args.fill_vf == 0:
                    fuse_str = fuse_str.zfill(147456)
                else:
                    fuse_str = "{0:1>147456}".format(fuse_str)
            else:
                fuse_str.zfill(147456)

    fuse_string.write(fuse_str.rstrip())
