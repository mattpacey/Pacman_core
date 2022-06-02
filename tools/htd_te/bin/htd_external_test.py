from htd_basic_flow import *


class EXTERNAL_TEST(htd_base_flow):
    def __init__(self, flow_num):
        htd_base_flow.__init__(self, self.__class__.__name__, flow_num)
        self.arguments.declare_arg("test_path", "The path to file define a test sequence in SPF or ITPP formats", "string", "none", 1)

    def flow_run(self):
        if os.path.splitext(self.arguments.get_argument("test_path"))[1] in ['.spf', '.espf']:
            self.exec_spf_action({"actionName": "SPF_TEST", "spf_file": self.arguments.get_argument("test_path")})
        else:
            self.exec_itpp_action({"actionName": "ITPP_TEST", "itpp_file": self.arguments.get_argument("test_path")})
