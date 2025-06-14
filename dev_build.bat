pyinstaller ^
--hidden-import=tiktoken_ext.openai_public --hidden-import=tiktoken_ext ^
--collect-all=pymdownx ^
--add-data="resources/*;resources/" -n "PyQtChat" ^
--onefile --collect-data=litellm --distpath="./dist/dev" ^
--icon resources\icon.ico main.py 