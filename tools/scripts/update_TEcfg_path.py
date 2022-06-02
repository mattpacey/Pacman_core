#!/usr/intel/bin/python2.7 -B


import os
import sys
import os.path
import argparse
import tempfile
import getpass
import string
import re
import xml.etree.cElementTree as ET
from xml.etree.ElementTree import Element, SubElement

sys.path.append(os.path.abspath("{}/../..".format(os.path.dirname(__file__))))
from tools.libs.helper_lib import *



class UpdatePacmanRoot(object):
    def __init__(self):

        parser = argparse.ArgumentParser(description='This script to update Pacman_root in TE.cfg to latest Pacman_root to run regression')
        parser.add_argument('-c', '--core', help='latest Pacman Root', required=True)
        parser.add_argument('-r', '--product', help='latest Htd_Root', required=True) 
        parser.add_argument('-p', '--prod', help='latest prod', required=True) 
        self.args = parser.parse_args()
        
    def run(self):
        self.update_htd_root()
    
    def update_htd_root(self):
        htd_root=self.args.product
        pacman_root=self.args.core
        prod=self.args.prod
        product_stepping = prod.split(',')
        for items in product_stepping:
            prod_htd_root=""
            project,step=items.strip().split('_')
            proj_step = "%s-%s" % (project,step)
        
            #complete TE config file path
            prod_htd_root = "%s/project/%s/htd_te_proj/TE_cfg.%s.xml" % (htd_root,project,proj_step)
            run_cmd("chmod 770 %s" % prod_htd_root)
        
            #print "Product_htd_root=%s" % (prod_htd_root)
            #print "pacman_root=%s" % (pacman_root)
        
            tree = ET.parse("%s" % (prod_htd_root))
            root = tree.getroot()
        
            for elem in root:
            
                if (elem.attrib.get("PACMAN_ROOT")):
                    new_root_dic = {'PACMAN_ROOT': '%s' % (pacman_root)}
                    elem.set("PACMAN_ROOT", "%s" % (pacman_root))
                
            tree.write("%s" % (prod_htd_root), "UTF-8")    
        
if __name__ == "__main__":
    upr=UpdatePacmanRoot()
    upr.run()

