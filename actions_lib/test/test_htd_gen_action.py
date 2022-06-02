#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B

import os
from os.path import join, dirname
import unittest
import sys
import pwd
import glob
import shutil
sys.path.append(join(dirname(sys.argv[0]), ".."))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))


from htd_gen_action import *
from htd_basic_action import *
from htd_basic_flow import *
from utils.files import TempDir
from utils.mock import patch, Mock, MagicMock
#from utils.ut import TestCase, unittest


class Test_htd_gen_action(unittest.TestCase):

    def setUp(self):
        actionName = "Wait4Mclk"
        sourceFile = "/nfs/sc/disks/mve_tvpv_029/tvpv/user_dir/beefongp/Master/mdo_cgf-pacman_core_repo/project/icxd/htd_te_proj/flows/stf_babystep.py"
        sourceLineno = 18
        currentFlow = "{TRY_TRACE}"
        is_internal = False
        self.gen_obj = GEN(actionName, sourceFile, sourceLineno, currentFlow, is_internal)
        pass

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

    def test_init(self):

        self.gen_obj.__init__("Wait4Mclk", "sourceFile", 18, "currentFlow", False)
        self.assertEquals(self.gen_obj.gen_action_types, ["WAIT", "PCOMMENT", "PINFO", "PLABEL", "ITPP", "SPF", "RATIO", "execute", "start_clock", "stop_clock"])
        self.assertEquals(self.gen_obj.arguments.arg_l['op']['description'], ("Gen action type.Supported types are: %s..") % (self.gen_obj.gen_action_types))
        self.assertEquals(self.gen_obj.arguments.arg_l['strvalue']['description'], "Used as a string parameter for PINFO,PLABEL,PCOMMENT,RATIO")

    def test_get_action_not_declared_argument_names(self):
        self.gen_obj.get_action_not_declared_argument_names()

    @patch("htd_gen_action.GEN.verify_obligatory_arguments")
    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='Test_Verify_Arguments')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_arguments_container.htd_argument_containter.set_obligatory')
    def test_verify_arguments(self, mock_obligatory, mock_lineno, mock_file, mock_name, mock_type, mock_verify_obligatory_arguments):

        # test op = WAIT
        self.gen_obj.arguments.set_argument('op', 'WAIT')
        self.gen_obj.verify_arguments()
        mock_obligatory.assert_any_call("waitcycles")
        mock_obligatory.assert_any_call("refclock")

        # test op in (["PCOMMENT","PINFO","PLABEL","ITPP","SPF", "RATIO", "execute", "start_clock", "stop_clock"])
        op_list = ["PCOMMENT", "PINFO", "PLABEL", "ITPP", "SPF", "RATIO", "execute", "start_clock", "stop_clock"]
        for op_value in op_list:
            self.gen_obj.arguments.set_argument('op', op_value)
            self.gen_obj.verify_arguments()
            mock_obligatory.assert_any_call('strvalue')

    # TODO: Python Error - need to solve while code cleanup
    @patch("htd_gen_action.GEN.verify_obligatory_arguments")
    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='Wait4Mclk')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_basic_action.htd_base_action.get_action_argument', return_value='INVALID')
    def test_verify_arguments_OP_INVALID(self, mock_arguments, mock_lineno, mock_file, mock_name, mock_type, mock_verify_obligatory_arguments):
        with self.assertRaises(AttributeError):
            self.gen_obj.verify_arguments()

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunWAIT')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_player_ui.htd_player_ui.wait_clock_num')
    def test_run_OP_WAIT_Pass(self, mock_clk_num, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "WAIT")
        self.gen_obj.arguments.set_argument("waitcycles", 100)
        self.gen_obj.arguments.set_argument("refclock", "bclk")
        mock_clk_num.assert_not_called(100, 'bclk')
        self.gen_obj.run()
        self.assertTrue(mock_clk_num.called)
        mock_clk_num.assert_called_with(100, 'bclk')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunPINFO')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.set_pattern_info')
    def test_run_OP_PINFO(self, mock_pattern_info, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "PINFO")
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        mock_pattern_info.assert_not_called('strvalue')
        self.gen_obj.run()
        self.assertTrue(mock_pattern_info.called)
        mock_pattern_info.assert_called_with('strvalue')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunPLABEL')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.label')
    def test_run_OP_PLABEL(self, mock_label, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "PLABEL")
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        mock_label.assert_not_called('strvalue')
        self.gen_obj.run()
        self.assertTrue(mock_label.called)
        mock_label.assert_called_with('strvalue', None)

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunPCOMMENT')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.add_comment')
    def test_run_OP_PCOMMENT(self, mock_comment, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "PCOMMENT")
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        mock_comment.assert_not_called('strvalue')
        self.gen_obj.run()
        self.assertTrue(mock_comment.called)
        mock_comment.assert_called_with('strvalue')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunSPF')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.write_spf_cmd')
    def test_run_OP_SPF(self, mock_spf, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "SPF")
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        mock_spf.assert_not_called('strvalue')
        self.gen_obj.run()
        self.assertTrue(mock_spf.called)
        mock_spf.assert_called_with('strvalue')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunITPP')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.write_itpp_cmd')
    def test_run_OP_ITPP(self, mock_itpp, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "ITPP")
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        mock_itpp.assert_not_called('strvalue')
        self.gen_obj.run()
        self.assertTrue(mock_itpp.called)
        mock_itpp.assert_called_with('strvalue')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunExecute')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.execute_signal')
    def test_run_OP_Execute(self, mock_execute, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "execute")
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        mock_execute.assert_not_called('strvalue')
        self.gen_obj.run()
        self.assertTrue(mock_execute.called)
        mock_execute.assert_called_with('strvalue')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRunRatio')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_gen_action.GEN.ratio_command')
    def test_run_OP_RATIO(self, mock_ratio, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "RATIO")
        mock_ratio.assert_not_called()
        self.gen_obj.run()
        self.assertTrue(mock_ratio.called)
        mock_ratio.assert_called_with()

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRun_StartClock_waitcycle100')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.start_clock')
    @patch('htd_hpl_spf_interface.hpl_spf_interface.wait_clock_num')
    def test_run_OP_StartClock_waitcycle100(self, mock_clk2, mock_startclk, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "start_clock")
        self.gen_obj.arguments.set_argument("waitcycles", 100)
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        self.gen_obj.arguments.set_argument("refclock", 'bclk')
        mock_startclk.assert_not_called("strvalue")
        mock_clk2.assert_not_called(100, 'bclk')
        self.gen_obj.run()
        self.assertTrue(mock_startclk.called)
        self.assertTrue(mock_clk2.called)
        mock_startclk.assert_called_with("strvalue")
        mock_clk2.assert_called_with(100, 'bclk')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRun_StartClock_waitcycle0')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.start_clock')
    @patch('htd_hpl_spf_interface.hpl_spf_interface.wait_clock_num')
    def test_run_OP_StartClock_with_waitcycle0(self, mock_clk2, mock_startclk, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "start_clock")
        self.gen_obj.arguments.set_argument("waitcycles", 0)
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        self.gen_obj.arguments.set_argument("refclock", 'bclk')
        mock_startclk.assert_not_called("strvalue")
        mock_clk2.assert_not_called(0, 'bclk')
        self.gen_obj.run()
        self.assertFalse(mock_clk2.called)
        self.assertTrue(mock_startclk.called)
        mock_startclk.assert_called_with("strvalue")
        mock_clk2.assert_not_called_with(0, 'bclk')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRun_StopClock_waitcycle100')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.stop_clock')
    @patch('htd_hpl_spf_interface.hpl_spf_interface.wait_clock_num')
    def test_run_OP_StopClock_with_waitcycle100(self, mock_clk3, mock_stopclk, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "stop_clock")
        self.gen_obj.arguments.set_argument("waitcycles", 100)
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        self.gen_obj.arguments.set_argument("refclock", 'bclk')
        mock_stopclk.assert_not_called("strvalue")
        mock_clk3.assert_not_called(100, 'bclk')
        self.gen_obj.run()
        self.assertTrue(mock_clk3.called)
        self.assertTrue(mock_stopclk.called)
        mock_stopclk.assert_called_with("strvalue")
        mock_clk3.assert_called_with(100, 'bclk')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRun_StopClock_waitcycle0')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_hpl_spf_interface.hpl_spf_interface.stop_clock')
    @patch('htd_hpl_spf_interface.hpl_spf_interface.wait_clock_num')
    def test_run_OP_StopClock_with_waitcycle0(self, mock_clk3, mock_stopclk, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument("op", "stop_clock")
        self.gen_obj.arguments.set_argument("waitcycles", 0)
        self.gen_obj.arguments.set_argument("strvalue", "strvalue")
        self.gen_obj.arguments.set_argument("refclock", 'bclk')
        mock_stopclk.assert_not_called("strvalue")
        mock_clk3.assert_not_called(0, 'bclk')
        self.gen_obj.run()
        self.assertTrue(mock_stopclk.called)
        self.assertFalse(mock_clk3.called)
        mock_stopclk.assert_called_with("strvalue")
        mock_clk3.assert_not_called_with(100, 'bclk')

    @patch('htd_basic_action.htd_base_action.get_action_type', return_value='GEN')
    @patch('htd_basic_action.htd_base_action.get_action_name', return_value='TestRun_InvalidOP')
    @patch('htd_basic_action.htd_base_action.get_action_call_file', return_value='sourceFile')
    @patch('htd_basic_action.htd_base_action.get_action_call_lineno', return_value=100)
    @patch('htd_logger.Logger.error')
    def test_run_OP_INVALID(self, mock_err_logger, mock_lineno, mock_file, mock_name, mock_type):
        self.gen_obj.arguments.set_argument('op', 'INVALID')
        self.gen_obj.run()
        expected_message = " [Wait4Mclk:sourceFile:100] Action's (Wait4Mclk) : Unsupported action type found - INVALID"
        mock_err_logger.assert_called_with(expected_message)

    @patch('htd_player_ui.htd_player_ui.restore_ratio')
    def test_ratio_command_restore(self, mock_restore):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"RatioClk": "dummyclk"}}):
            self.gen_obj.arguments.set_argument('strvalue', 'restore')
            mock_restore.assert_not_called()
            self.gen_obj.ratio_command()
            self.assertTrue(mock_restore.called)
            mock_restore.assert_call_with()

    @patch('htd_player_ui.htd_player_ui.set_ratio')
    def test_ratio_command_2(self, mock_ratio):
        with patch.dict('htd_collaterals_parser.CFG', {"HPL": {"RatioClk": "dummyclk"}}):
            self.gen_obj.arguments.set_argument('strvalue', '2')
            mock_ratio.assert_not_called(2, 'dummyclk')
            self.gen_obj.ratio_command()
            self.assertTrue(mock_ratio.called)
            mock_ratio.assert_called_with(2, 'dummyclk')

    @patch('htd_logger.Logger.error')
    def test_ratio_command_Invalid(self, mock_logger):
        self.gen_obj.arguments.set_argument('strvalue', 'invalid')
        self.gen_obj.ratio_command()
        expected_message = " [Wait4Mclk:stf_babystep.py:18] Can't set illegal integer value invalid as ratio"
        mock_logger.assert_called_with(expected_message)


if __name__ == '__main__':
    unittest.main()
