.\dist\Nikita\Nikita.exe stop
.\dist\Nikita\Nikita.exe remove

call b.2pyd.cmd

ren .\src\cherry.py cherry.p
ren .\src\*.py *.yp
ren .\src\cherry.p cherry.py

rmdir /S /Q .\dist\
rmdir /S /Q .\build\

set PYTHONOPTIMIZE=1 && ^
pyinstaller ..\Nikita\Nikita.py ^
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
--name=Nikita 

ren .\src\*.yp *.py
del .\src\*.pyd
rem goto start
rem --hidden-import dictionaries ^
rem --key=tc2lanruoJ ^
rem del .\dist\Nikita\mkl*.dll

mkdir .\dist\Nikita\java
mkdir .\dist\Nikita\solr
xcopy .\java .\dist\Nikita\java /s/h/e/k/f/c
xcopy .\solr-8.2.0 .\dist\Nikita\solr /s/h/e/k/f/c

rem move .\dist\Nikita\vcruntime140.dll .\dist\Nikita\vcruntime140.dl
rem upx-x .\dist\Nikita\*.exe
rem upx-x .\dist\Nikita\*.dll
rem upx-x .\dist\Nikita\*.pyd
rem move .\dist\Nikita\vcruntime140.dl .\dist\Nikita\vcruntime140.dll

:start
.\dist\Nikita\Nikita.exe remove
rem .\dist\Nikita\Nikita.exe install
rem .\dist\Nikita\Nikita.exe start