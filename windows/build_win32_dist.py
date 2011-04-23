from distutils.core import setup
import py2exe
import shutil
shutil.rmtree('dist', True)
setup(windows=['main.py'], script_args=['py2exe'])
shutil.move('dist/main.exe', 'dist/spesmilo.exe')
