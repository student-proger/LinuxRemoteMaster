pyinstaller --icon=mainicon.ico --noconsole main.py
md dist\main\images
copy images\*.* dist\main\images\
copy license dist\main\
copy changelog.txt dist\main\
rename dist\main\main.exe lrm.exe
rename dist\main\main.exe.manifest lrm.exe.manifest