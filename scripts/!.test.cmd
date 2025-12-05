cd /d "%~dp0\.."
rmdir /S /Q .\dist\
rmdir /S /Q .\build\

set PYTHONOPTIMIZE=1 && ^
pyinstaller ..\Journal2ct\Journal2Ct.py ^
--onedir ^
--console ^
--clean ^
--exclude-module numpy ^
--exclude-module cryptography ^
--exclude-module lib2to3 ^
--exclude-module win32com ^
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
--name=Journal2ct 

copy .\dlls\*.dll .\dist\Journal2ct\

.\dist\Journal2ct\Journal2ct.exe