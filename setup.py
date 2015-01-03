__author__ = 'Paul Mason'

import sys
import constants
from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
   base = 'Win32GUI'

options = {
    'build_exe': {
        "include_msvcr": True
    },
    # the upgrade-code ensures newer versions update over older ones rather than creating new copies in Control Panel
    'bdist_msi' : {
        'upgrade_code' : '{AA28BF7F-EA75-4324-A5E8-CC5B72F3E5E6}'
    }
}

executables = [
    Executable('SC930_LRQ.py', base=None), # Console version
    Executable('SC930_LRQ_gui.py', base=base, shortcutName='SC930_LRQ',shortcutDir='DesktopFolder') #GUI
]

setup(name='SC930_LRQ',
      version=constants.SC930_LRQ_VER,
      description="SC930 Long-Running Query Finder",
      author='Actian Corporation',
      url=constants.SC930_LRQ_LINK,
      options=options,
      executables=executables
      )