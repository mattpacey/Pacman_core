#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python
"""
unittest for htd_uCPL_action.py, product template
"""
import os
from os.path import join, dirname
import unittest
import sys
import pwd
import glob
import shutil
sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))

#from utils.ut import unittest
from utils.mock import patch, MagicMock, patchobject, patchdict, Mock
from htd_uCPL_action import *
from htd_basic_flow import *
from htd_basic_action import *
from htd_utilities import *
from htd_collaterals import *
from htd_player_top import *
from utils.helperclass import CaptureStdoutLog


class Test_htd_uCPL_action(unittest.TestCase):
    def test(self):
        pass
#    def setUp(self):
#        actionName = "test_ucpl"
#        sourceFile = '/nfs/png/disks/mdo_tvpv_073/calebtec/pacman/mdo_cgf-product_code/project/knhcpu/htd_te_proj/flows/ucpl_babystep.py'
#        sourceLineno = 9
#        currentFlow  = "{TRY_TRACE}"
#        is_internal = False
#        sbft_mode = "mlc"
#        self.ucpl_obj = UCPL(actionName,sourceFile,sourceLineno,currentFlow,is_internal)
#        pass

    def tearDown(self):
        idsid = pwd.getpwuid(os.getuid()).pw_name
        tmp = '/tmp/*' + idsid + '*'
        tmp_dir = glob.glob(tmp)

        for items in tmp_dir:
            if ('run_all_tests') in items:
                pass

            else:
                if os.path.isdir(items):
                    shutil.rmtree(items)
                elif os.path.exists(items):
                    os.remove(items)


#    def test_init(self):
#        self.ucpl_obj.__init__("test_ucpl","sourceFile",18,"currentFlow",False)
#
#    def test_get_action_not_declared_argument_names(self):
#        self.ucpl_obj.get_action_not_declared_argument_names()
#        pass
#
#    def test_verify_arguments_error0(self):
#        os.environ['HTD_COLLECT_RTL_SIGNALS_MODE'] = '1'
#        self.ucpl_obj.verify_arguments()
#        os.environ.pop('HTD_COLLECT_RTL_SIGNALS_MODE')
#
#    def test_verify_arguments_error1(self):
#        os.environ.pop('VTTSTSRC')
#        with self.assertRaises(SystemExit) as cm:
#            with CaptureStdoutLog() as log:
#                self.ucpl_obj.verify_arguments()
#            self.assertIn('Missing obligatory unix environment ENV[HTD_SBFT_UCPL_LOCATION] - must point to HTD CPL path')
#        os.environ['VTTSTSRC'] = '/p/hdk/rtl/valid/shdk74/tests'
#
#    def test_verify_arguments_error2(self):
#        os.environ.pop('HTD_SBFT_UCPL_LOCATION')
#        with self.assertRaises(SystemExit) as cm:
#            with CaptureStdoutLog() as log:
#                self.ucpl_obj.verify_arguments()
#            self.assertIn("Missing obligatory unix environment ENV[HTD_SBFT_UCPL_LOCATION] - must point to HTD CPL path")
#        os.environ['HTD_SBFT_UCPL_LOCATION'] = '/nfs/png/disks/mdo_tvpv_073/calebtec/pacman/mdo_cgf-product_code/tools/htd_ucpl'
#
#    def test_verify_arguments_error3(self):
#        os.environ.pop('HTD_SBFT_CPL_TRIGGER_SIGNAL')
#        with self.assertRaises(SystemExit) as cm:
#            with CaptureStdoutLog() as log:
#                self.ucpl_obj.verify_arguments()
#            self.assertIn( 'Missing obligatory unix environment ENV[HTD_SBFT_CPL_TRIGGER_SIGNAL] - must provide Trigger signal for CPL/SLP handshake')
#        os.environ['HTD_SBFT_CPL_TRIGGER_SIGNAL'] = 'soc_tb.soc.cnxnorthxcc.northcap012.pmrctop.pmsrvr_ioregsp.ebctop.hvm_message[63:0]'
#
#    def test_verify_arguments_error4(self):
#        os.environ.pop('HTD_SBFT_UCPL_MLC_OPTION')
#        with self.assertRaises(SystemExit) as cm:
#            with CaptureStdoutLog() as log:
#                self.ucpl_obj.verify_arguments()
#            self.assertIn( 'Missing obligatory unix environment ENV[HTD_SBFT_UCPL_MLC_OPTION] - must indicate the type on cache on the Core IP: L2 or MLC, needed for injections')
#        os.environ['HTD_SBFT_UCPL_MLC_OPTION'] = 'MLC'
#
#    def test_verify_arguments_error5(self):
#        os.environ.pop('HTD_SBFT_CPL_OUTPUT_FILE_NAME')
#        with self.assertRaises(SystemExit) as cm:
#            with CaptureStdoutLog() as log:
#                self.ucpl_obj.verify_arguments()
#            self.assertIn( 'Missing obligatory unix environment ENV[HTD_SBFT_CPL_OUTPUT_FILE_NAME] - cpl default name ')
#        os.environ['HTD_SBFT_CPL_OUTPUT_FILE_NAME'] = 'cpl.txt'
#
#    # @patch('htd_uCPL_action.UCPL.input_file', return_value= 'text.32.obj')
#    # # @patch('htd_arguments_container.htd_argument_containter.get_argument')
#    # def test_verify_arguments_run1(self, mock_argu):
#    #     print mock_argu.return_value
#    #     self.ucpl_obj.input_file = "sdas.32.obj"
#    #     # self.ucpl_obj.obj_file = "textname.32.obj"
#    #     self.ucpl_obj.verify_arguments()
#
#
#        # self.assertEqual(mock_get_argu.call_count, 5)
#    #     self.assertIn( 'Missing obligatory unix environment ENV[HTD_SBFT_CPL_OUTPUT_FILE_NAME] - cpl default name ')
#
#
#    # @patch.dict(os.environ, {'HTD_COLLECT_RTL_SIGNALS_MOD': '1'})
#    # @patch("htd_uCPL_action.arguments.", return_value=1)
#    # def test_run_return(self):
#    #     self.ucpl_obj.run()
#
#    # @patch('htd_uCPL_action.UCPL.sbft_mode', return_value= 'UCPL.SBFT_MODE_MLC')
#    # def test_run_spf2itpp(self, mock_sbftmode):
#    #     self.ucpl_obj.run_spf2itpp()
#
#
#    def test_run_spf_action(self):
#        self.ucpl_obj.spf_file = 'test.spf'
#        self.ucpl_obj.run_spf_action()
#        self.assertEqual(self.ucpl_obj.output_file, self.ucpl_obj.spf_file)
#
#
#    @patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "spf"}})
#    @patch('htd_uCPL_action.UCPL.set_spf_file_iswat')
#    def test_get_output_file_name_mci_spf(self, mock_setspf):
#        self.ucpl_obj.spf_file = "test.spf"
#        mock_cpl = "test.cpl"
#        self.ucpl_obj.get_output_file_name_mci(mock_cpl)
#        mock_setspf.assert_called_with(mock_cpl)
#
#    @patch.dict('htd_collaterals_parser.CFG', {"HPL": {"execution_mode": "itpp"}})
#    @patch('htd_uCPL_action.UCPL.set_spf_file_iswat')
#    def test_get_output_file_name_mci_itpp(self, mock_setspf):
#        self.ucpl_obj.spf_file = "test.spf"
#        mock_cpl = "test.cpl"
#        self.ucpl_obj.get_output_file_name_mci(mock_cpl)
#        mock_setspf.assert_called_with(mock_cpl)
#
#    @patch('htd_arguments_container.htd_argument_containter.get_argument')
#    def test_set_spf_file_iswat(self, mock_argu):
#        mock_cpl = "test.cpl"
#        self.ucpl_obj.set_spf_file_iswat(mock_cpl)
#
if __name__ == '__main__':
    unittest.main()
