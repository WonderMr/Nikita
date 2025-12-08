cd /d "%~dp0\.."
rmdir /s /q solr
rmdir /s /q debug
mkdir solr
mkdir debug
xcopy /e /y solr-src solr
del /q Nikita.ini
del /q *.state
