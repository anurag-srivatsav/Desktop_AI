Set WshShell = CreateObject("WScript.Shell")
' Get the current user's desktop path
strPath = CreateObject("WScript.Shell").SpecialFolders("Desktop") & "\Desktop_ai"
' Run the batch file with the full path
WshShell.Run chr(34) & strPath & "\start_assistant.bat" & chr(34), 0
Set WshShell = Nothing 