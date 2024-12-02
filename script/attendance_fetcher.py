import requests
from datetime import datetime, timedelta

class AttendanceFetcher:
    def __init__(self, base_url, headers, session=None):
        self.base_url = base_url
        self.headers = headers
        self.session = session or requests.Session()

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
            print("Не удалось получить CSRF-токен из печеньки")
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

    def process_visits_data(self, visits_data):
        if not visits_data:
            return []

        all_visits = []
        for state in ['APPROVED', 'MISSED']:
            visits = visits_data.get(state, [])
            for visit in visits:
                start_time = datetime.strptime(visit['start_time'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=5)
                all_visits.append({
                    'Имя': f"{visit['first_name']} {visit['last_name']}",
                    'Дата рождения': visit['birthday'],
                    'Дата': start_time.strftime('%d.%m'),
                    'Время': start_time.strftime('%H:%M'),
                    'Центр': 'Robocode',
                    'Занятие': visit['lesson'],
                    'Статус': 'V' if state == 'APPROVED' else '',
                })
        return all_visits

    def get_approved_visits(self, visits_data):
        approved_visits = visits_data.get('APPROVED', [])
        result = []
        for visit in approved_visits:
            result.append({
                'Имя': f"{visit['first_name']} {visit['last_name']}",
                'approve_timestamp': visit.get('approve_timestamp')
            })
        return result
