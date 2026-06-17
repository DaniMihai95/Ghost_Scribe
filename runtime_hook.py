"""
PyInstaller runtime hook for OpenVINO
Sets up environment BEFORE any imports
"""
import os
import sys

if getattr(sys, 'frozen', False):
    # Get the base directory
    if hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(sys.executable), "_internal")
    
    # OpenVINO libs directory
    ov_libs = os.path.join(base, "openvino", "libs")
    ov_genai = os.path.join(base, "openvino_genai")
    ov_tokenizers = os.path.join(base, "openvino_tokenizers")
    
    # Set OpenVINO environment variables BEFORE any imports
    os.environ['OPENVINO_LIB_PATH'] = ov_libs
    os.environ['OV_FRONTEND_PATH'] = ov_libs
    
    # Add to DLL search paths
    if hasattr(os, 'add_dll_directory'):
        if os.path.exists(ov_libs):
            os.add_dll_directory(ov_libs)
        if os.path.exists(ov_genai):
            os.add_dll_directory(ov_genai)
        if os.path.exists(ov_tokenizers):
            os.add_dll_directory(ov_tokenizers)
    
    # Update PATH
    paths = [ov_libs, ov_genai, ov_tokenizers, os.environ.get('PATH', '')]
    os.environ['PATH'] = ";".join(p for p in paths if p)
