# import modules
from ast import parse
import os
import argparse

# import internal modules
from Menu import *
from Utils import *
from gui import *
from cli import *


def main():
    parser = argparse.ArgumentParser(
        prog="TimeTracker",
        description="Working IN and OUT time tracker"
    )
    parser.add_argument('-u', '--ui', choices=['gui', 'cli'], default='cli')
    args = parser.parse_args()

    if os.environ.get('ANDROID_ROOT') is not None or args.ui == 'gui':
        gui = Gui()
        gui.run()
    else:
        cli = Cli()
        cli.run()


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt) as e:
        pass
    except:
        myassert(False, "An exception has occurred.", True)
