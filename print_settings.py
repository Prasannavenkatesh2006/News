import os
import sys
sys.path.insert(0, os.path.abspath('src'))
os.chdir('C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main')

from anip.config import settings
print(f"DB Host: {settings.database.host}")
print(f"DB User: {settings.database.user}")
print(f"DB Password: {settings.database.password}")
print(f"DB Name: {settings.database.db}")
