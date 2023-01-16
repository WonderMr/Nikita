@echo off
netsh advfirewall firewall show rule name="Nikita"
if errorlevel 1 Goto add
echo firewall rule exists
exit
:add
echo creating firewall rule
netsh.exe advfirewall firewall add rule name="Nikita" dir=in action=allow protocol=TCP localport=8984
