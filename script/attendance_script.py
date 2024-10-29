import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import calendar


class AttendanceFetcher:
    def __init__(self, headers):
        self.headers = headers
        self.base_url = 'https://api.prod.yaya.kz'
        self.session = requests.Session()  # Используем сессию для хранения куков

    def get_csrf_session_token(self, username, password):
        login_url = f'{self.base_url}/admin/login/?next=/admin/visits'
        response = self.session.get(login_url)

        if 'csrftoken' in self.session.cookies:
            csrf_token = self.session.cookies['csrftoken']
            print(f"Получен CSRF-токен: {csrf_token}")
            login_data = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf_token
            }

            headers = {
                'Cookie': f'csrftoken={csrf_token}',
                'Referer': login_url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
            }
            auth_response = self.session.post(login_url, data=login_data, headers=headers)
            if auth_response.status_code == 200 and 'sessionid' in self.session.cookies:
                print("Успешная авторизация")
                return True
            else:
                print(f"Ошибка авторизации: {auth_response.status_code}")
                return False
        else:
            print("Не удалось получить CSRF-токен из куков")
            return False

    def fetch_visits(self, date):
        visits_url = f'{self.base_url}/admin/visit/load_all_visits/?center_id=819&date={date}&lesson_ids=%5B%222093%22%2C%222092%22%2C%222091%22%5D&lesson_colors=%7B%222091%22%3A%22%23376FFF%22%2C%222092%22%3A%22%234DB4FF%22%2C%222093%22%3A%22%23293A78%22%7D'
        response = self.session.get(visits_url, headers=self.headers)
        if response.status_code == 200:
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError as e:
                print(f"Ошибка JSONDecodeError: {e}")
                print("Ответ от API:", response.text)
        else:
            print(f"Ошибка: Код ответа {response.status_code}")
            print("Ответ от API:", response.text)
        return None

    def process_data(self, visits_data):
        if visits_data is None:
            print("Данные отсутствуют или произошла ошибка при запросе.")
            return []

        visited = visits_data.get('APPROVED', [])
        missed = visits_data.get('MISSED', [])

        visited_data = [
            {
                'Имя': f"{visit['first_name']} {visit['last_name']}",
                'Дата рождения': visit['birthday'],
                'Время': datetime.strptime(visit['start_time'].replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S%z').strftime(
                    '%d.%m'),
                'Центр': 'Robocode',
                'Занятие': visit['lesson'],
                'Статус': 'V'
            }
            for visit in visited
        ]

        missed_data = [
            {
                'Имя': f"{visit['first_name']} {visit['last_name']}",
                'Дата рождения': visit['birthday'],
                'Время': datetime.strptime(visit['start_time'].replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S%z').strftime(
                    '%d.%m'),
                'Центр': 'Robocode',
                'Занятие': visit['lesson'],
                'Статус': ''
            }
            for visit in missed
        ]

        return visited_data + missed_data


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

    def update_sheet(self, worksheet, data):
        col_values = worksheet.col_values(5)
        today = datetime.today().strftime('%d.%m')

        if today in col_values:
            print("Данные уже загружены")
        else:
            next_filled_row = len(col_values) + 1
            df = pd.DataFrame(data)
            values = df.values.tolist()
            cell_range = f'C{next_filled_row}'
            worksheet.update(range_name=cell_range, values=values)
            print("Данные успешно загружены в Google Sheets.")


if __name__ == "__main__":
    username = "7074224239"
    password = "Je1FrzknSm"

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://api.prod.yaya.kz/admin/visits/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

    # Файл с учетными данными для Google Sheets
    credentials_file = r'C:\Users\Tao\PycharmProjects\attendance-script\script\config\spreadsheet.json'
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1SXfpTJ2TJglApMAKGf6u-x_8q_p9zQdfAm2QlmDNZd4/edit#gid=143358604"

    attendance_fetcher = AttendanceFetcher(headers)

    if attendance_fetcher.get_csrf_session_token(username, password):
        today_date = datetime.today().strftime('%Y-%m-%d')
        visits_data = attendance_fetcher.fetch_visits(today_date)
        processed_data = attendance_fetcher.process_data(visits_data)

        google_sheet_updater = GoogleSheetUpdater(credentials_file, spreadsheet_url)
        worksheet = google_sheet_updater.get_worksheet()
        google_sheet_updater.update_sheet(worksheet, processed_data)
