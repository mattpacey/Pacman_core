import re
from htd_utilities import *
from htd_collaterals import *
from htd_te_shared import *
import csv
import atexit

# -----------------------
#
# ------------------------


class htd_action_statistics(object):
    # ----------------------
    def __init__(self):
        self.csvfile = open('htd_statistics.csv', 'w')
        self.csvwriter = csv.writer(self.csvfile)
        self.row_db = []
        self.__saved = 0
        self.header = []

    description = "The htd_statistics class collects statistical information per action "
    author = "alexse"

    # ---------------------
    def append_new_column(self, name):
        if (name not in self.header):
            self.header.append(name)
            # --------------------------------

    def capture_statistics(self, action_ptr):
        if (action_ptr.is_inner_action()):
            return
        self.append_new_column("action_name")
        self.append_new_column("action_type")
        for arg in action_ptr.get_declared_arguments():
            if (arg not in self.header):
                self.header.append(arg)
                for r in self.row_db:
                    r.append("-")
        # ------------------------------
        self.interactive = 0
        self.non_interactive = 0
        self.determine_if_interactive(action_ptr)
        self.append_new_column("interactive")
        self.append_new_column("non_interactive")
        # ------------------------------
        self.append_new_column("start_time")
        self.append_new_column("end_time")
        self.append_new_column("start_model_time")
        self.append_new_column("end_model_time")
        # -----------------------------------------
        self.append_new_column("documented")  # --The information of register is matched user requirest
        self.append_new_column("implicit_rtl_nodes_exists")  # --The explicit field rtl node - user specified
        self.append_new_column(
            "explicit_rtl_nodes_exists")  # --The implicit field rtl node - complimentory  to user specified
        self.append_new_column("ready4rmw")  # --   implicit_rtl_nodes_status +
        self.append_new_column("ready4check")  # --   implicit_rtl_nodes_status +  explicit_rtl_nodes_status
        self.append_new_column("ready4injection")  # --   explicit_rtl_nodes_status
        # ---------------------------------
        self.append_new_column("documented_details")
        self.append_new_column("implicit_rtl_details")
        self.append_new_column("explicit_rtl_details")
        # -----------------------

        new_row = []
        for h in self.header:
            if (h == "action_name"):
                new_row.append(action_ptr.get_action_name())
            elif (h == "action_type"):
                new_row.append(action_ptr.get_action_type())
            elif (h == "interactive"):
                new_row.append(self.interactive)
            elif (h == "non_interactive"):
                new_row.append(self.non_interactive)
            elif (h == "start_time"):
                new_row.append(str(action_ptr.action_time_start))
            elif (h == "end_time"):
                new_row.append(str(action_ptr.action_time_end))
            elif (h == "start_model_time"):
                new_row.append(str(action_ptr.action_model_time_start))
            elif (h == "end_model_time"):
                new_row.append(str(action_ptr.action_model_time_end))
            # ---------------
            elif (h == "documented"):
                new_row.append(action_ptr.documented)
            elif (h == "implicit_rtl_nodes_exists"):
                new_row.append(action_ptr.implicit_rtl_nodes_exists if action_ptr.documented else "0")
            elif (h == "explicit_rtl_nodes_exists"):
                new_row.append(action_ptr.explicit_rtl_nodes_exists if action_ptr.documented else "0")
            elif (h == "ready4rmw"):
                new_row.append(action_ptr.implicit_rtl_nodes_exists if action_ptr.documented else "0")
            elif (h == "ready4check"):
                new_row.append((
                               action_ptr.implicit_rtl_nodes_exists and action_ptr.explicit_rtl_nodes_exists) if action_ptr.documented else "0")
            elif (h == "ready4injection"):
                new_row.append(action_ptr.explicit_rtl_nodes_exists if action_ptr.documented else "0")
            elif (h == "documented_details"):
                new_row.append(action_ptr.documented_details)
            elif (h == "implicit_rtl_details"):
                new_row.append(action_ptr.implicit_rtl_details)
            elif (h == "explicit_rtl_details"):
                new_row.append(action_ptr.explicit_rtl_details)
            else:
                if (h not in list(action_ptr.arguments.arg_l.keys())):
                    new_row.append("-")
                else:
                    new_row.append(str(action_ptr.arguments.get_argument(h)))
        self.row_db.append(new_row)

    # ------------------------
    def snoop_csv_file(self):
        if (not self.__saved):
            self.row_db.insert(0, self.header)
            self.csvwriter.writerows(self.row_db)
            self.csvfile.close()
            self.__saved = 1

    def determine_if_interactive(self, action_ptr):
        if action_ptr.argument_exists('silent_mode') and action_ptr.argument_exists('dummy'):
            self.interactive = (
                not action_ptr.get_action_argument('silent_mode') and not action_ptr.get_action_argument(
                    'dummy'))  # if not dummy and not silent mode --> this is an action which is enabled for simulation
            self.non_interactive = (
                action_ptr.get_action_argument('silent_mode') and not action_ptr.get_action_argument(
                    'dummy'))  # if not dummy and silent mode --> action runs non_interactively, but hasn't neen enabled for interactive run (sim/emu)


# -------------------
HTD_STATISTICS_MGR = htd_action_statistics()


def snoop_statistics_file():
    HTD_STATISTICS_MGR.snoop_csv_file()


# define the at exit handler to properly close statistics file upon exit
atexit.register(snoop_statistics_file)
