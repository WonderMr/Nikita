cd /d "%~dp0\.."
.\dist\Journal2ct\Journal2ct.exe stop
.\dist\Journal2ct\Journal2ct.exe remove

call b.2pyd.cmd

ren .\src\cherry.py cherry.p
ren .\src\*.py *.yp
ren .\src\cherry.p cherry.py

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

ren .\src\*.yp *.py
del .\src\*.pyd
rem goto start
rem --hidden-import dictionaries ^
rem --key=tc2lanruoJ ^
rem del .\dist\Journal2ct\mkl*.dll

rem .\dist\Journal2ct\Journal2ct.exe
rem exit

mkdir .\dist\Journal2ct\java
mkdir .\dist\Journal2ct\solr
xcopy .\java .\dist\Journal2ct\java /s/h/e/k/f/c
xcopy .\solr-src .\dist\Journal2ct\solr /s/h/e/k/f/c
mkdir .\dist\Journal2ct-StarForce-ready
xcopy .\dist\Journal2ct .\dist\Journal2ct-StarForce-ready /s/h/e/k/f/c

rem move .\dist\Journal2ct\vcruntime140.dll .\dist\Journal2ct\vcruntime140.dl
rem upx-x .\dist\Journal2ct\*.exe
rem upx-x .\dist\Journal2ct\*.dll
rem upx-x .\dist\Journal2ct\*.pyd
rem move .\dist\Journal2ct\vcruntime140.dl .\dist\Journal2ct\vcruntime140.dll

:start
.\dist\Journal2ct\Journal2ct.exe remove
rem .\dist\Journal2ct\Journal2ct.exe install
rem .\dist\Journal2ct\Journal2ct.exe start