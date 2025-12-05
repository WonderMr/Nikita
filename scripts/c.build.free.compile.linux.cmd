cd /d "%~dp0\.."
call b.2pyd.cmd

ren .\src\cherry.py cherry.p
ren .\src\*.py *.yp
ren .\src\cherry.p cherry.py

rmdir /S /Q .\dist\
rmdir /S /Q .\build\

set PYTHONOPTIMIZE=1 && ^
pyinstaller %CD%\Nikita.py ^
-D -F ^
--onedir ^
--console ^
--clean ^
--exclude-module numpy ^
--exclude-module cryptography ^
--exclude-module lib2to3 ^
--exclude-module win32com ^
--exclude-module gevent ^
--exclude-module matplotlib ^
--exclude-module matplotlib.backend ^
--hidden-import subprocess ^
--hidden-import cherrypy ^
--hidden-import urllib ^
--hidden-import threading ^
--hidden-import requests ^
--hidden-import re ^
--hidden-import time ^
--hidden-import operator ^
--hidden-import json ^
--hidden-import psutil ^
--hidden-import subprocess ^
--hidden-import shlex ^
--hidden-import platform ^
--hidden-import socket ^
--hidden-import sqlite3 ^
--hidden-import src.parser ^
--hidden-import src.reader ^
--hidden-import src.dictionaries ^
--hidden-import src.messenger ^
--log-level DEBUG ^
--name=Nikita 

ren .\src\*.yp *.py
del .\src\*.pyd
mkdir .\dist\Nikita-StarForce-ready
xcopy .\dist\Nikita .\dist\Nikita-StarForce-ready /s/h/e/k/f/c