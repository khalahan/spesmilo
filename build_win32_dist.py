from distutils.core import setup
import py2exe
import shutil
shutil.rmtree('dist', True)
setup(windows=['main.py'], script_args=['py2exe'])
for d in ('i18n', 'icons'):
	shutil.copytree(d, 'dist/%s' % (d,))
for f in ('bitcoind.exe', 'libeay32.dll'):
	shutil.copy(f, 'dist/%s' % (f,))
shutil.move('dist/main.exe', 'dist/spesmilo.exe')
