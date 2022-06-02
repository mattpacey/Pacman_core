#!/usr/intel/pkgs/python3/3.6.3a/modules/r1/bin/python  -B
from htd_unix_socket import *


class htd_test_server(htd_unix_socket_server):
    def __init__(self, server_name, debug_mode=0):
        htd_unix_socket_server.__init__(self, server_name)

    def request_handler(self, data):
        print(("Server:Got a request data:%s") % (data))
        self.send("PASS|Response Done")


# ---------------------------------------
serv = htd_test_server("TestServer", "SimServerSocket")
