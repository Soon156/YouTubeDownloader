import sys
from cx_Freeze import setup, Executable

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="YouTube Downloader",
    version='0.0.2',
    description="YouTube Downloader",
    executables=[Executable("main.py", base=base, icon="")],
)
