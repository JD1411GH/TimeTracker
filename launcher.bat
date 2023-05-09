@echo off
rem Just create the shortcut to the batch file, then go to its properties, and change target from "C:\path-to-your-batch" to cmd.exe /k "path-to-your-batch"
rem After that, the icon of the shortcut changes and you can drop it on the taskbar to pin it.
echo Fetching data from google sheet
python main.py
exit