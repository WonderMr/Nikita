rmdir /s /q solr
rmdir /s /q debug
mkdir solr
mkdir debug
xcopy /e /y solr-src solr
del /q journal2ct.ini
del /q *.state
