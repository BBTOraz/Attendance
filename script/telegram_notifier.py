# telegram_notifier.py

from telethon import TelegramClient

class TelegramNotifier:
    def __init__(self, api_id, api_hash, bot_token, chat_id):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.client = None

    async def __aenter__(self):
        self.client = TelegramClient('bot_session', self.api_id, self.api_hash)
        await self.client.start(bot_token=self.bot_token)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.disconnect()

    async def send_message(self, message):
        await self.client.send_message(self.chat_id, message)
