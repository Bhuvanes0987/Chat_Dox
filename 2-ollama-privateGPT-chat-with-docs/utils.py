# utils.py
import os

def does_vectorstore_exist(persist_directory):
    return os.path.exists(persist_directory)
