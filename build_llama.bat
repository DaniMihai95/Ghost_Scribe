@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d C:\Users\suntd\Documents\Projects\Articles\Article1
call venv\Scripts\activate.bat
set CMAKE_ARGS=-DGGML_CUDA=on
pip install llama-cpp-python --no-cache-dir
