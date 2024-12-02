import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('YAYA_USERNAME')
password = os.getenv("PASSWORD")
credentials_file = os.getenv("CREDENTIALS_FILE")
spreadsheet_url = os.getenv("SPREADSHEET_URL")
telegram_api_id = os.getenv("TELEGRAM_API_ID")
telegram_api_hash = os.getenv("TELEGRAM_API_HASH")
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_chat_id = int(os.getenv('TELEGRAM_CHAT_ID'))

print("USERNAME:", username)
print("PASSWORD:", password)
print("CREDENTIALS_FILE:", credentials_file)
print("SPREADSHEET_URL:", spreadsheet_url)
print("TELEGRAM_API_ID:", telegram_api_id)
print("TELEGRAM_API_HASH:", telegram_api_hash)
print("TELEGRAM_BOT_TOKEN:", telegram_bot_token)
print("TELEGRAM_CHAT_ID:", telegram_chat_id)
