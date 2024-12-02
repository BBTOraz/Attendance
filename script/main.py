# main.py

import os
from datetime import datetime, time as dt_time, timedelta
from attendance_fetcher import AttendanceFetcher
from google_sheet_updater import GoogleSheetUpdater
from conf import (
    credentials_file, spreadsheet_url,
    telegram_api_id, telegram_api_hash, telegram_bot_token,
    telegram_chat_id, username, password
)
from telegram_notifier import TelegramNotifier
import asyncio


async def main():
    base_url = "https://api.prod.yaya.kz"
    headers = {"User-Agent": "Mozilla/5.0"}

    print("Current working directory:", os.getcwd())

    attendance_fetcher = AttendanceFetcher(base_url, headers)
    google_sheet_updater = GoogleSheetUpdater(credentials_file, spreadsheet_url)

    if not attendance_fetcher.get_csrf_session_token(username, password):
        print("Не удалось авторизоваться")
        return

    while True:
        now = datetime.now()
        if dt_time(10, 0) <= now.time() <= dt_time(23, 59):
            today_date = now.strftime('%Y-%m-%d')
            visits_data = attendance_fetcher.fetch_visits(today_date)
            if visits_data:
                processed_data = attendance_fetcher.process_visits_data(visits_data)
                worksheet = google_sheet_updater.get_worksheet()
                google_sheet_updater.update_sheet(worksheet, processed_data)

                approved_visits = attendance_fetcher.get_approved_visits(visits_data)
                sent_messages = google_sheet_updater.get_sent_messages()
                async with TelegramNotifier(telegram_api_id, telegram_api_hash, telegram_bot_token, telegram_chat_id) as telegram_notifier:
                    for visit in approved_visits:
                        name = visit['Имя']
                        approve_timestamp = visit['approve_timestamp']

                        message_key = f"{name}_{approve_timestamp}"
                        approved_time = datetime.strptime(visit['approve_timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(hours=5)
                        if message_key not in sent_messages:
                            message = (
                                f"Пользователь {name} посетил занятие."
                                f" Время подтверждения: {approved_time.strftime('%H:%M')}"
                            )
                            try:
                                await telegram_notifier.send_message(message)
                                print(f"Сообщение для {name} отправлено.")

                                google_sheet_updater.add_sent_message(name, approve_timestamp)
                                sent_messages.add(message_key)
                            except Exception as e:
                                print(f"Ошибка при отправке сообщения для {name}: {e}")
                        else:
                            print(f"Сообщение для {name} с approve_timestamp {approved_time.strftime('%H:%M')} уже было отправлено.")
            else:
                print("Нет данных посещений")
            await asyncio.sleep(300)
        else:
            print("Не рабочее время, скрипт ждет...")
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
