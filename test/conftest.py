# back_end/test/conftest.py
import sys
import os

# أضف مجلد back_end للمسار
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
