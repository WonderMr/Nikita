cd /d "%~dp0\.."
call c.build.1.compile.cmd
call d.1.StarForced.before.cmd
"C:\Program Files (x86)\Protection Studio 2\ProtectionStudio.exe" -WorkspaceId:22437 -Project:c:\Repos\Nikita\protection_studio_project.psf -Action:ProtectFiles -Log:c:\Repos\Nikita\protection_studio_project.log
call d.3.StarForced.after.cmd
"C:\Program Files (x86)\NSIS\makensisw.exe" "C:\Repos\Nikita\c.installer.nsi"