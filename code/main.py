# SciSafeEval Main
import os
import sys
sys.path.append(os.getcwd() + "/garak")
from garak import cli

if __name__ == "__main__":
    cli.main(sys.argv[1:])