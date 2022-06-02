#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python -B

import os
from os.path import join, dirname
import unittest
import sys
import pwd
import glob
import shutil
#from utils.ut import TestCase, unittest
from utils.mock import patch, Mock, MagicMock
from utils.helperclass import CaptureStdoutLog

sys.path.append(join(dirname(__file__), ".."))
sys.path.append(os.getenv('PACMAN_ROOT'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'tools/htd_te/bin'))
sys.path.append(join(os.getenv('PACMAN_ROOT'), 'htd_info'))

from htd_ubptrigger_action import *
from htd_basic_flow import *
import htd_collaterals_parser
unittest_flow = htd_base_flow("unittest_ubp", 1)


class TestHtdUbpTriggerAction(unittest.TestCase):
    def setUp(self):
        # action_name, source_file, source_lineno, currentFlow, is_internal
        self.test_obj = UBPTRIGGER("test_ubptrigger", "ubptrigger_file", 10, unittest_flow, False)

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
        self.test_obj.__init__("test_ubptrigger", "ubptrigger_file", 10, unittest_flow, False)

        # case of TE has tap_mode
        with patch.dict(htd_collaterals_parser.CFG["TE"], {"tap_mode": "test_tap_mode"}):
            with self.assertRaises(SystemExit):
                with CaptureStdoutLog() as log:
                    self.test_obj.__init__("test_ubptrigger", "ubptrigger_file", 10, unittest_flow, False)
            self.assertIn("Illegal TAP protocol type selection in CFG[\"TE\"][\"tap_mode\"]", log.getvalue())
            self.assertEqual(self.test_obj.tap_protocol, "test_tap_mode")

    @patch("htd_ubptrigger_action.UBPTRIGGER.get_curr_flow")
    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_fields", return_value=["test_field_1"])
    def test_send_tap_flow(self, mock_get_ir_fields, mock_get_curr_flow):
        self.test_obj.ir_name = "test_ir_name"
        self.test_obj.ir_agent = "test_ir_agent"
        self.test_obj.fields = {"test_field_1": 0x1, "test_field_a": 0x2}

        self.test_obj.send_tap_flow()
        mock_get_ir_fields.assert_called_with("test_ir_name", "test_ir_agent")
        mock_get_curr_flow.assert_called()

    @patch("htd_ubptrigger_action.UBPTRIGGER.send_tap_flow")
    def test_send_tap_array(self, mock_send_tap_flow):
        self.test_obj.tap_cmds = [
            {
                "ir": "test_ir",
                "agent": "test_agent",
                "check": self.test_obj.check,
                "rmw": self.test_obj.read_modify_write,
                "bfm": self.test_obj.bfm_mode,
                "fields": {"test_field_1": 0x1, "test_field_a": 0x2}
            }
        ]

        self.test_obj.send_tap_array()
        self.assertEqual(self.test_obj.ir_name, "test_ir")
        self.assertEqual(self.test_obj.check, self.test_obj.check)
        self.assertEqual(self.test_obj.read_modify_write, self.test_obj.read_modify_write)
        self.assertEqual(self.test_obj.bfm_mode, self.test_obj.bfm_mode)
        self.assertEqual(self.test_obj.fields, {"test_field_1": 0x1, "test_field_a": 0x2})
        self.assertEqual(self.test_obj.labels, {})
        self.assertEqual(self.test_obj.mask, {})
        self.assertEqual(self.test_obj.strobe, {})
        self.assertEqual(self.test_obj.capture, {})
        mock_send_tap_flow.assert_called()

    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_opcode_int", return_value=0)
    def test_check_tap_var_ircode_eq_0(self, mock_get_ir_opcode_int):
        self.test_obj.ir_agent = "test_ir_agent"

        # for case of ir_name is none
        self.test_obj.ir_name = ""
        self.test_obj.check_tap_var()
        mock_get_ir_opcode_int.assert_not_called()

        mock_get_ir_opcode_int.mock_reset()

        # for case of ir_name is not none
        self.test_obj.ir_name = "test_ir_name"
        self.test_obj.check_tap_var()
        self.assertEqual(self.test_obj.documented, 0)
        self.assertIn("Unknown TAP agent", self.test_obj.documented_details)

    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_name", return_value="")
    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_opcode_int", return_value=-1)
    def test_check_tap_var_ircode_lr_0(self, mock_get_ir_opcode_int, mock_get_ir_name):
        self.test_obj.ir_agent = "test_ir_agent"
        self.test_obj.ir_name = "test_ir_name"
        self.test_obj.check_tap_var()
        mock_get_ir_opcode_int.assert_called_with("test_ir_name", "test_ir_agent", self.test_obj.dummy_mode)
        mock_get_ir_name.assert_not_called()

    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_name", return_value="")
    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_opcode_int", return_value=1)
    def test_check_tap_var_ircode_gr_0_irname_none(self, mock_get_ir_opcode_int, mock_get_ir_name):
        self.test_obj.ir_agent = "test_ir_agent"
        self.test_obj.ir_name = "test_ir_name"
        self.test_obj.check_tap_var()
        self.assertEqual(self.test_obj.documented, 0)
        self.assertIn("Cant get TAP agent", self.test_obj.documented_details)

    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_name", return_value="test_dummy")
    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_opcode_int", return_value=1)
    def test_check_tap_var_ircode_gr_0_irname_dummy(self, mock_get_ir_opcode_int, mock_get_ir_name):
        self.test_obj.ir_agent = "test_ir_agent"
        self.test_obj.ir_name = "test_ir_name"
        self.test_obj.check_tap_var()
        mock_get_ir_opcode_int.assert_called_with("test_ir_name", "test_ir_agent", self.test_obj.dummy_mode)
        mock_get_ir_name.assert_called_with(1, "test_ir_agent", self.test_obj.dummy_mode)

    @patch("htd_ubptrigger_action.HTD_INFO.tap_info.get_ir_commands", return_value=["BRKPTEN1", "test_field"])
    def test_action_enable(self, mock_get_ir_commands):
        self.test_obj.Actions_Dictionary = {
            "test_ubp_action_1": {"UBP": "Dummy"},
            "test_ubp_action_2": {"UBP": "BRKPTCTL1", "IP": "test_IP"}
        }

        # case of not defined BRK register
        self.test_obj.action_enable("test_ubp_action_1", True)
        mock_get_ir_commands.assert_not_called()
        self.assertEqual(self.test_obj.tap_cmds, [])

        mock_get_ir_commands.mock_reset()

        # case of actual passing input
        self.test_obj.action_enable("test_ubp_action_2", True)
        mock_get_ir_commands.assert_called()
        tap_cmds_result = [{
            "manual": 1,
            "ir": "BRKPTEN1",
            "agent": "test_IP",
            "check": 1,
            "rmw": 1,
            "bfm": "tap",
            "fields": {".*ENABLE.*|.*brk.*en.*": True},
        }]
        self.assertEqual(self.test_obj.tap_cmds, tap_cmds_result)

    def test_debug_readback(self):
        self.test_obj.debug_readback()

    def test_get_action_not_declared_argument_names(self):
        self.test_obj.get_action_not_declared_argument_names()

    def test_mbp_to_trigger(self):
        # case with MBP trigger
        self.test_obj.Actions_Dictionary["EDRAM_ubp"] = {
            "ACTION": {"SO_LOAD_TOGGLE": "1", "array_freeze": "1"},
            "TRIGGER": {"MBP": "0x1"},
            "UBP": "BRKPTCTL1"
        }
        self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.assertEqual(self.test_obj.mbp_pin_triggers[0], [0, 1])

        # reset parameter
        self.test_obj.mbp_pin_triggers = {}

        # case with fabric_triggers
        self.test_obj.Actions_Dictionary["EDRAM_ubp"] = {
            "ACTION": {"SO_LOAD_TOGGLE": "1", "array_freeze": "1"},
            "TRIGGER": {"fabric_triggers": "0x2"},
            "UBP": "BRKPTCTL1"
        }
        self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.assertEqual(self.test_obj.mbp_pin_triggers[1], [0, 1])

        # case with cluster_model
        tmp = self.test_obj.cluster_model_mode
        self.test_obj.cluster_model_mode = 1
        # reset parameter
        self.test_obj.mbp_pin_triggers = {}
        self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.test_obj.cluster_model_mode = tmp
        self.assertEqual(self.test_obj.mbp_pin_triggers[1], [1, 0])

        # case with trigger_by_tap
        self.test_obj.arguments.set_argument("trigger_by_tap", True)

        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.assertIn("while missing Action[\"TAP_TRIGGER_CMD\"]", log.getvalue())

        tap_action = {
            "actionName": "UbpActiontest_ubp_action_TriggerByTap",
            "agent": "CDU_PUNIT_TAP",
            "ir": "MBPCONFIG",
            "MBP_ENABLE": "0x1",
            "MANUAL_MBP": "0x2"
        }
        exp = {
            'CDU_PUNIT_TAP': {'MBPCONFIG': {'actionName': '_UbpActiontest_ubp_action_TriggerByTap',
                                            'MANUAL_MBP': '0x2',
                                            'MBP_ENABLE': '0x1'}}
        }
        self.test_obj.Actions_Dictionary["EDRAM_ubp"] = {
            "ACTION": {"SO_LOAD_TOGGLE": "1", "array_freeze": "1"},
            "TRIGGER": {"MBP": "0x1", "fabric_triggers": "0x2"},
            "UBP": "BRKPTCTL1",
            "TAP_TRIGGER_CMD": tap_action
        }
        self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.assertEqual(self.test_obj.mbp_tap_triggers, exp)

        # case with chord
        self.test_obj.Actions_Dictionary["EDRAM_ubp"] = {
            "ACTION": {"SO_LOAD_TOGGLE": "1", "array_freeze": "1"},
            "TRIGGER": {"CHORD": "0x2"},
            "UBP": "CHORDCTL1"
        }
        self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.assertEqual(self.test_obj.chord_pin_triggers[0][2], ['0', '0', '1', '0', '0', '1'])

        # case with cluster_model
        tmp = self.test_obj.cluster_model_mode
        self.test_obj.cluster_model_mode = 1
        # reset parameter
        self.test_obj.chord_pin_triggers = {}
        self.test_obj.mbp_to_trigger(["EDRAM_ubp"])
        self.test_obj.cluster_model_mode = tmp
        self.assertEqual(self.test_obj.chord_pin_triggers[0][13], ['1', '1', '0', '1', '1', '0'])

    @patch("htd_ubptrigger_action.UBPTRIGGER.mbp_to_trigger")
    def test_verify_ubp_action(self, mock_mbp_to_trigger):
        # check missing ubp action
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.verify_ubp_action()
        self.assertIn("Missing tap sequence \"bit0\" index...", log.getvalue())

        # check ubp action not defined in Actions_Dictionary
        self.test_obj.arguments.set_argument("Ubp_action", "test_ubp_action_1")
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.verify_ubp_action()
        self.assertIn("UBP action - \"test_ubp_action_1\" not defined", log.getvalue())

        # check mbp_to_trigger call
        self.test_obj.Actions_Dictionary = {
            "test_ubp_action_1": {"UBP": "BRKPTCTL1", "IP": "test_IP"}
        }
        self.test_obj.verify_ubp_action()
        mock_mbp_to_trigger.assert_called_with(["test_ubp_action_1"])

    @patch("htd_ubptrigger_action.UBPTRIGGER.verify_ubp_action")
    @patch("htd_ubptrigger_action.UBPTRIGGER.inform")
    def test_verify_arguments(self, mock_inform, mock_verify_ubp_action):
        # function doesn't have hard pass/fail requirement, hence checking here is just assert call
        def reset():
            mock_verify_ubp_action.mock_reset()
            mock_inform.mock_reset()
            # reset variable for next test
            self.test_obj.Actions_Dictionary = {}

        # case without force tap
        self.test_obj.verify_arguments()
        mock_verify_ubp_action.assert_called()
        # values are defined during init
        mock_inform.assert_called_with("       Verifying UBPTRIGGER::test_ubptrigger:ubptrigger_file:10 ....")

        reset()

        # case with force tap: pass case
        CFG["TE"]["ubp_trigger_by_tap_only"] = 1
        self.test_obj.verify_arguments()
        mock_verify_ubp_action.assert_called()
        mock_inform.assert_called_with(" Found CFG[\"TE\"][\"ubp_trigger_by_tap_only\"]=1... Enforcing ubp_trigger_by_tap_only=1.. ")

        reset()

        # case with force tap: fail case
        # overriding TAP_TRIGGER_CMD to force fail test
        CFG["UBP_actions"]["EDRAM_ubp"]["TAP_TRIGGER_CMD"] = ""
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.verify_arguments()
        self.assertIn("Trying to use trigger by tap cmd , while missing CFG", log.getvalue())
        mock_verify_ubp_action.assert_called()
        mock_inform.assert_called_with(" Found CFG[\"TE\"][\"ubp_trigger_by_tap_only\"]=1... Enforcing ubp_trigger_by_tap_only=1.. ")

        reset()

        # case with force tap but trigger not MBP
        CFG["UBP_actions"]["EDRAM_ubp"]["TRIGGER"] = "IP_match:0x1234"
        self.test_obj.verify_arguments()
        mock_verify_ubp_action.assert_called()
        mock_inform.assert_called_with(" Found CFG[\"TE\"][\"ubp_trigger_by_tap_only\"]=1... Enforcing ubp_trigger_by_tap_only=1.. ")

    def test_parse_tap_trigger_cmd(self):
        # case of pass
        action = "test_ubp_action"
        cmd = "CDU_PUNIT_TAP.MBPCONFIG:MBP_ENABLE=0x1,MANUAL_MBP=0x2"
        exp = {
            "actionName": "UbpActiontest_ubp_action_TriggerByTap",
            "agent": "CDU_PUNIT_TAP",
            "ir": "MBPCONFIG",
            "MBP_ENABLE": "0x1",
            "MANUAL_MBP": "0x2"
        }
        res = self.test_obj.parse_tap_trigger_cmd(action, cmd)

        self.assertEqual(res, exp)

        # case of incorrect length
        cmd = "dummy"
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.parse_tap_trigger_cmd(action, cmd)
        self.assertIn("Improper format found for CFG[\"UBP_actions\"]", log.getvalue())

        # case of incorrect TAP cmd format
        cmd = "tap_only:field=0x1"
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.parse_tap_trigger_cmd(action, cmd)
        self.assertIn("Improper TAP cmd format found for CFG[\"UBP_actions\"]", log.getvalue())

        # case of incorrect TAP field format
        cmd = "tap.reg:field_only"
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.parse_tap_trigger_cmd(action, cmd)
        self.assertIn("Improper TAP cmd:field format found for CFG[\"UBP_actions\"]", log.getvalue())

    def test_get_product_setup(self):
        # case without pickle
        self.test_obj.get_product_setup()
        res = {'EDRAM_ubp': {'ACTION': {'SO_LOAD_TOGGLE': '1', 'array_freeze': '1'},
                             'ACTION_STR': 'SO_LOAD_TOGGLE:1,array_freeze:1',
                             'ALLOW_TOG': '',
                             'CONFIGURED': 0,
                             'ENABLED': 0,
                             'IP': 'EDRAM',
                             'REARM': 0,
                             'TAP_TRIGGER_CMD': {'MANUAL_MBP': '0x2',
                                                 'MBP_ENABLE': '1',
                                                 'actionName': 'UbpActionEDRAM_ubp_TriggerByTap',
                                                 'agent': 'CDU_PUNIT_TAP',
                                                 'ir': 'MBPROOTCONFIG'},
                             'TRIGGER': {'MBP': '0x1', 'fabric_triggers': '0x2'},
                             'TRIGGER_STR': 'MBP:0x1,fabric_triggers:0x2',
                             'UBP': 'BRKPTCTL1'}}
        self.assertEqual(self.test_obj.Actions_Dictionary, res)

        # case with single action
        self.test_obj.Actions_Dictionary = {}
        with patch.dict(htd_collaterals_parser.CFG["UBP_actions"]["EDRAM_ubp"], {"ACTION": "SO_LOAD_TOGGLE:1"}):
            self.test_obj.get_product_setup()
            self.assertEqual(self.test_obj.Actions_Dictionary["EDRAM_ubp"]["ACTION"], {"SO_LOAD_TOGGLE": "1"})

    action_dict = {
        'EDRAM_ubp': {'UBP': 'BRKPTCTL1',
                      'REARM': 0,
                      'IP': 'EDRAM',
                      'TRIGGER_STR': 'MBP:0x1,fabric_triggers:0x2',
                      'ACTION_STR': 'SO_LOAD_TOGGLE:1,array_freeze:1',
                      'ALLOW_TOG': ''}
    }

    @patch("htd_ubptrigger_action.htd_history_mgr.parametric_table_get", return_value=action_dict)
    @patch("htd_ubptrigger_action.htd_history_mgr.parametric_has_table", return_value=True)
    def test_get_product_setup_pickle(self, mock_parametric_has_table, mock_parametric_table_get):
        res = {
            'EDRAM_ubp': {'UBP': 'BRKPTCTL1',
                          'REARM': 0,
                          'IP': 'EDRAM',
                          'TRIGGER_STR': 'MBP:0x1,fabric_triggers:0x2',
                          'TAP_TRIGGER_CMD': {'MANUAL_MBP': '0x2',
                                              'MBP_ENABLE': '1',
                                              'actionName': 'UbpActionEDRAM_ubp_TriggerByTap',
                                              'agent': 'CDU_PUNIT_TAP',
                                              'ir': 'MBPROOTCONFIG'},
                          'ACTION_STR': 'SO_LOAD_TOGGLE:1,array_freeze:1',
                          'ALLOW_TOG': ''}
        }
        self.test_obj.get_product_setup()
        self.assertEqual(self.test_obj.Actions_Dictionary, res)

        def per_key_check(key, msg=None):
            with patch.dict(htd_collaterals_parser.CFG["UBP_actions"]["EDRAM_ubp"], {key: "dummy"}):
                with self.assertRaises(SystemExit):
                    with CaptureStdoutLog() as log:
                        self.test_obj.get_product_setup()
                if not msg:
                    msg = key
                self.assertIn(msg + " in this action diff from TE_CFG to pickle", log.getvalue())

        per_key_check("IP")
        per_key_check("UBP")
        per_key_check("TRIGGER")
        per_key_check("ACTION")
        per_key_check("REARM")
        per_key_check("ALLOW_TOG", "Allow together")    # special error msg

    def test_print_current_ubps(self):
        self.test_obj.Actions_Dictionary = {
            "test_ubp_action_1": {
                "ENABLED": 0,
                "CONFIGURED": 1,
                "IP": "test_ip_1, test_ip_2",
                "TRIGGER": {"test_mbp_1": 0x1, "test_mbp_2": 0x2},
                "UBP": "test_brkptctl"
            },
        }
        self.test_obj.print_current_ubps()
        # TODO: how to check the comment printing?

    @patch("htd_basic_flow.htd_base_flow.get_ip_name", return_value="testip")
    @patch("htd_basic_flow.htd_base_flow.exec_action")
    def test_setsignal(self, mock_exec_action, mock_get_ip_name):
        # case of mbp_pin not cluster model
        htd_collaterals_parser.CFG["MBP_setting"] = {"MBP_WAITCYCLES": 4}
        self.test_obj.get_curr_flow().unset_verify_mode()
        self.test_obj.mbp_pin_triggers[0] = [0, 1]
        self.test_obj.setsignal()
        mock_exec_action.assert_called_with(
            {'xxMBP_0': 1, 'refclock': 'bclk', 'waitcycles': 1, 'check': 0, 'op': 'FORCE'},
            'SIG', 'UBPTRIGGER', 0, 'test_ubptrigger'
        )
        # TODO: how to check multiple call of exec_action? for loop and MBP_WAITCYCLES

        # case with cluster model
        mock_exec_action.reset()
        self.test_obj.cluster_model_mode = True
        htd_collaterals_parser.CFG["FlowSignals"]["testipMBP0"] = "testipxxMBP_0"
        self.test_obj.setsignal()
        mock_exec_action.assert_called_with(
            {'postalignment': 0, 'refclock': 'tclk', 'waitcycles': 13, 'postdelay': 0, 'op': 'WAIT'},
            'GEN', 'UBPTRIGGER', 0, 'test_ubptrigger'
        )
        self.test_obj.cluster_model_mode = False

        # case of chord
        mock_exec_action.reset()
        self.test_obj.mbp_pin_triggers = {}
        self.test_obj.chord_pin_triggers[0] = {'0': [1, 1, 0, 1, 1, 0]}
        self.test_obj.setsignal()
        mock_exec_action.assert_called_with(
            {'xxMBP_0': 0, 'refclock': 'bclk', 'waitcycles': 1, 'check': 0, 'op': 'FORCE'},
            'SIG', 'UBPTRIGGER', 0, 'test_ubptrigger'
        )

        # case with cluster model
        mock_exec_action.reset()
        self.test_obj.cluster_model_mode = True
        self.test_obj.setsignal()
        mock_exec_action.assert_called_with(
            {'xxMBP_0': 0, 'refclock': 'bclk', 'waitcycles': 1, 'check': 0, 'op': 'FORCE'},
            'SIG', 'UBPTRIGGER', 0, 'test_ubptrigger'
        )
        self.test_obj.cluster_model_mode = False

        # case of tap
        mock_exec_action.reset()
        self.test_obj.chord_pin_triggers = {}
        # FIXME: below has been coded in accordance to actual TAP action, mocking it could simplify this
        self.test_obj.mbp_tap_triggers = {
            'EDRAM': {'TAPSTATUS': {'actionName': '_UbpActiontest_ubp_action_TriggerByTap',
                                    'STOP_EDCLK_STATUS': '0x1'}}
        }
        self.test_obj.setsignal()
        mock_exec_action.assert_called_with(
            {'actionName': '_UbpActiontest_ubp_action_TriggerByTap',
             'ir': 'TAPSTATUS',
             'agent': 'EDRAM',
             'incremental_mode': 1,
             'STOP_EDCLK_STATUS': '0x1', },
            'TAP', 'UBPTRIGGER', 0, 'test_ubptrigger'
        )

    @patch("htd_ubptrigger_action.UBPTRIGGER.setsignal")
    @patch("htd_ubptrigger_action.UBPTRIGGER.send_tap_array")
    @patch("htd_ubptrigger_action.UBPTRIGGER.action_enable")
    @patch("htd_ubptrigger_action.UBPTRIGGER.inform")
    @patch("htd_ubptrigger_action.UBPTRIGGER.print_current_ubps")
    @patch("htd_ubptrigger_action.UBPTRIGGER.get_product_setup")
    def test_run(self, mock_get_product_setup, mock_print_current_ubps, mock_inform,
                 mock_action_enable, mock_send_tap_array, mock_setsignal):
        self.test_obj.ubp_action_l = ["test_ubp"]

        # case with both enabled and configured, rearm
        self.test_obj.Actions_Dictionary["test_ubp"] = {"ENABLED": 1, "CONFIGURED": 1, "REARM": 1}
        self.test_obj.run()
        mock_setsignal.assert_called()
        self.assertEqual(self.test_obj.Actions_Dictionary["test_ubp"]["ENABLED"], 1)

        # case with both enabled and configured, no rearm
        mock_setsignal.reset()
        self.test_obj.Actions_Dictionary["test_ubp"] = {"ENABLED": 1, "CONFIGURED": 1, "REARM": 0}
        self.test_obj.run()
        mock_setsignal.assert_called()
        self.assertEqual(self.test_obj.Actions_Dictionary["test_ubp"]["ENABLED"], 0)

        # case with not enabled (with force_enable) and configured
        mock_setsignal.reset()
        self.test_obj.Actions_Dictionary["test_ubp"] = {"ENABLED": 0, "CONFIGURED": 1, "REARM": 0}
        self.test_obj.arguments.set_argument("force_enable", 1)
        self.test_obj.run()
        mock_setsignal.assert_called()
        mock_action_enable.assert_called()
        mock_send_tap_array.assert_called()
        self.assertEqual(self.test_obj.Actions_Dictionary["test_ubp"]["ENABLED"], 0)

        # case with not enabled, not configured, and duplicated trigger
        mock_action_enable.reset()
        self.test_obj.Actions_Dictionary["test_ubp"] = {"ENABLED": 0, "CONFIGURED": 0, "TRIGGER_STR": "dummy"}
        self.test_obj.Actions_Dictionary["test_ubp2"] = {"ENABLED": 1, "CONFIGURED": 0, "TRIGGER_STR": "dummy"}
        with self.assertRaises(SystemExit):
            with CaptureStdoutLog() as log:
                self.test_obj.run()
        self.assertIn("You're trying to trigger", log.getvalue())
        self.assertEqual(mock_action_enable.call_count, 2)

        pass


if __name__ == '__main__':
    unittest.main()
