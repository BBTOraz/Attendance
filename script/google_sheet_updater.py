import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import calendar

class GoogleSheetUpdater:
    def __init__(self, credentials_file, spreadsheet_url):
        self.credentials_file = credentials_file
        self.spreadsheet_url = spreadsheet_url
        self.client = self.authorize()

    def authorize(self):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, scope)
        return gspread.authorize(credentials)

    def get_worksheet(self):
        spreadsheet = self.client.open_by_url(self.spreadsheet_url)

        current_month = datetime.today().month
        month_name = calendar.month_name[current_month]
        month_name_ru = {
            'January': 'Январь',
            'February': 'Февраль',
            'March': 'Март',
            'April': 'Апрель',
            'May': 'Май',
            'June': 'Июнь',
            'July': 'Июль',
            'August': 'Август',
            'September': 'Сентябрь',
            'October': 'Октябрь',
            'November': 'Ноябрь',
            'December': 'Декабрь'
        }.get(month_name, month_name)

        worksheet_name = f"YaYa {month_name_ru}"

        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"Лист '{worksheet_name}' уже существует.")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=26)
            print(f"Лист '{worksheet_name}' был создан.")

        return worksheet

    def get_message_storage_worksheet(self):
        spreadsheet = self.client.open_by_url(self.spreadsheet_url)
        try:
            worksheet = spreadsheet.worksheet('MessageStorage')
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title='MessageStorage', rows=1000, cols=3)
            worksheet.append_row(['Имя', 'approve_timestamp', 'Дата'])
            print("Лист 'MessageStorage' был создан.")
        return worksheet

    def get_sent_messages(self):
        worksheet = self.get_message_storage_worksheet()
        records = worksheet.get_all_records()
        sent_messages = set(f"{record['Имя']}_{record['approve_timestamp']}" for record in records)
        return sent_messages

    def add_sent_message(self, name, approve_timestamp):
        worksheet = self.get_message_storage_worksheet()
        date = datetime.today().strftime('%d.%m.%Y')
        worksheet.append_row([name, approve_timestamp, date])

    def update_sheet(self, worksheet, data):
        today = datetime.today().strftime('%d.%m')
        df_new = pd.DataFrame(data)
        df_new['Дата'] = df_new['Дата'].astype(str)

        all_values = worksheet.get_all_values()

        columns = ['Имя', 'Дата рождения', 'Дата', 'Время', 'Центр', 'Занятие', 'Статус']

        if all_values:
            all_values_trimmed = [row[2:] for row in all_values]

            for i, row in enumerate(all_values_trimmed):
                if len(row) < len(columns):
                    all_values_trimmed[i] += [''] * (len(columns) - len(row))
                elif len(row) > len(columns):
                    all_values_trimmed[i] = row[:len(columns)]
            df_existing = pd.DataFrame(all_values_trimmed, columns=columns)
        else:
            df_existing = pd.DataFrame(columns=columns)

        df_existing['Дата'] = df_existing['Дата'].astype(str)
        df_today = df_existing[df_existing['Дата'] == today]

        df_today_sorted = df_today.sort_values(by=columns).reset_index(drop=True)
        df_new_sorted = df_new.sort_values(by=columns).reset_index(drop=True)

        if df_today_sorted.equals(df_new_sorted):
            print("Данные за сегодня уже актуальны. Обновление не требуется.")
        else:
            print("Обнаружены изменения в данных за сегодня. Обновляем данные.")
            indices_to_delete = df_existing.index[df_existing['Дата'] == today].tolist()

            rows_to_delete = [i + 1 for i in indices_to_delete]

            for row in sorted(rows_to_delete, reverse=True):
                worksheet.delete_rows(row)

            total_rows = len(worksheet.get_all_values())
            next_row = total_rows + 1

            values = df_new[columns].values.tolist()

            num_rows = len(values)
            num_cols = len(columns)

            start_col_letter = 'C'
            end_col_letter = chr(ord(start_col_letter) + num_cols - 1)
            end_row = next_row + num_rows - 1

            cell_range = f'{start_col_letter}{next_row}:{end_col_letter}{end_row}'

            worksheet.update(cell_range, values)
            print("Данные успешно обновлены в Google Sheets.")


