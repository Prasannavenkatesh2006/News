import sys
import os
import traceback
from dotenv import load_dotenv

os.chdir('C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main')
load_dotenv('.env')

sys.path.insert(0, 'C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/src')
sys.path.insert(0, 'C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main/services/api')
os.environ['POSTGRES_HOST'] = '127.0.0.1'

from app.social.routes import get_feed

try:
    feed = get_feed(limit=30, offset=0, community_slug=None, sentiment=None, sort='importance')
    print("Feed length:", len(feed))
except Exception as e:
    traceback.print_exc()
