from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': ['sys', 'time', 'sqlite3', 'os', 'PyQt5.QtWidgets', 'PyQt5.uic', 'PyQt5.QtCore', 'PyQt5.QtGui', 'datetime', 'telegram', 'rank', 'threading', 'requests', 'urllib.parse', 'pandas', 'notice', 'apscheduler'], 'excludes': []}

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('main.py', base=base, icon="./ui/logo.ico")
]

setup(name='naver-shopping',
      version = '1.7',
      description = '네이버쇼핑순위봇1',
      options = {'build_exe': build_options},
      executables = executables)