#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B
import subprocess


def print_info(msg):
    print("-I- {}".format(msg))


def print_warning(msg):
    print("-W- {}".format(msg))


def print_error(msg, code=1):
    print("-E- {}".format(msg))
    exit(code)


def run_cmd(cmd, err_check=1, return_data=0):
    print_info(cmd)
    child = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

    while child.poll() is None and return_data == 0:
        output = child.stdout.readline()
        print_info(output.rstrip())

    # This will catch any remaining stdout that the while loop didn't catch
    output = child.communicate()[0]
    print_info(output)

    exitcode = child.returncode

    if (exitcode != 0 and err_check == 1):
        print_error("Error running command. Return code: %d" % (exitcode))
    elif (exitcode != 0):
        return None
    return output
