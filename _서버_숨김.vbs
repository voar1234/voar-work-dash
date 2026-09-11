' 로그온 시 대시보드 server.py 를 콘솔 창 없이 백그라운드로 실행
Dim shell, fso, scriptDir, srvPath
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
srvPath = scriptDir & "\server.py"
' pythonw.exe = 콘솔 없이 실행. python.exe 는 창이 뜸.
shell.Run "pythonw.exe -X utf8 """ & srvPath & """", 0, False
