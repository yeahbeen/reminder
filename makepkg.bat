pyinstaller reminder.py --clean --distpath="./pyinstaller/dist" --workpath="./pyinstaller/build" --add-data="sound;sound" --add-data="picture;picture" --add-data="cherry.ico;." --icon="cherry.ico" --noconfirm -w
xcopy pyinstaller\dist\reminder reminder\ /E /Y
pause