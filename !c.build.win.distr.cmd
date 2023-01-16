cls
.\dist\Nikita\Nikita.exe stop
.\dist\Nikita\Nikita.exe remove

del .\src\*.pyd
python b.compiles2pyd.py build_ext --inplace
if %errorlevel% neq 0 exit /b %errorlevel%

ren .\src\cherry.py cherry.p
ren .\src\*.py *.yp
ren .\src\cherry.p cherry.py

rmdir /S /Q .\dist\
rmdir /S /Q .\build\

set PYTHONOPTIMIZE=1 && ^
pyinstaller .\Nikita.py ^
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
--exclude-module __PyInstaller_hooks_0_pandas_io_formats_style ^
--hidden-import subprocess ^
--hidden-import clickhouse_driver ^
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
--hidden-import win32timezone ^
--hidden-import src.dictionaries ^
--hidden-import src.messenger ^
--log-level DEBUG ^
--name=Nikita 

copy .\dlls\*.dll .\dist\Nikita\

ren .\src\*.yp *.py
del .\src\*.pyd


mkdir .\dist\Nikita\java
mkdir .\dist\Nikita\solr
xcopy .\java .\dist\Nikita\java /s/h/e/k/f/c
xcopy .\solr-src .\dist\Nikita\solr /s/h/e/k/f/c

.\dist\Nikita\Nikita.exe remove
"C:\Program Files (x86)\NSIS\makensisw.exe" %CD%\c.installer.nsi"