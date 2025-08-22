from cx_Freeze import setup, Executable

# base="Win32GUI" should be used only for Windows GUI app
base = None

setup(
    name="LearningApp",
    version="0.1",
    description="My Learning Application!",
    executables=[Executable("src/main.py", base=base)],
)
