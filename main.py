# import modules
import os
import argparse
import platform

# import internal modules
from menu import *
from utils import *
from gui import *
from cli import *


def main():
    parser = argparse.ArgumentParser(
        prog="TimeTracker",
        description="Working IN and OUT time tracker"
    )
    parser.add_argument('-u', '--ui', choices=['gui', 'cli'], default='cli')
    args = parser.parse_args()

    # using platform.machine() to detect android
    # hope to find a cleaner way in future
    if platform.machine() == 'aarch64' or args.ui == 'gui':
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
