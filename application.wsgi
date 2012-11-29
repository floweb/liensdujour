import os, sys

PROJECT_DIR = '/var/www/flask-liensdujour'

activate_this = os.path.join(PROJECT_DIR, 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))
sys.path.append(PROJECT_DIR)

from liensdujour import app as application