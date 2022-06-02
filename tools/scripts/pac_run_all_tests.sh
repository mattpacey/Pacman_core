#!/usr/intel/bin/tcsh
echo sourcing HTDVAL ...
setenv cmd "source $1/sourceme -p htdval -s a0"
$cmd -cmd
echo source HTDVAL complete ...
echo setting PACMAN_ROOT ...
pwd
setenv PACMAN_ROOT `pwd`
echo set PACMAN_ROOT complete ...
echo start pac_run_all_tests ...
tools/scripts/pac_run_all_tests.py
set result = $status
echo done pac_run_all_tests ...

if ("$result" == 0) then
    echo "passing pac_run_all_test"
    exit 0
else
    echo "failing pac_run_all_test"
    exit 1
endif
