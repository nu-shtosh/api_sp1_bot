import logging
import os
import time

import requests
from requests import RequestException
import telegram
from dotenv import load_dotenv

load_dotenv()
os.path.expanduser('~')

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
LOGGER = logging.getLogger(__name__)

PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
if PRAKTIKUM_TOKEN is None:
    LOGGER.debug('Токен отсутсвует!')
    raise ValueError('Токен отсутсвует!')

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

TG_BOT = telegram.Bot(token=TELEGRAM_TOKEN)
YAP_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
AUTH_YAP_TOKEN = f'OAuth {PRAKTIKUM_TOKEN}'
HEADERS = {'Authorization': AUTH_YAP_TOKEN}

STATUS_ERROR = 'Ошибка статуса!'
NONE_ERROR = 'STATUS OR HOMEWORK IS NONE'
STATUSES = {
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, работа зачтена!',
    'reviewing': 'Вашу работу проверяют.',
}


def parse_homework_status(homework):
    HW_NAME = homework.get('homework_name')
    HW_STATUS = homework.get('status')

    if HW_NAME is None or HW_STATUS is None:
        raise ValueError(NONE_ERROR)

    REVIEWING = f'У вас проверили работу "{HW_NAME}"!\n\n{STATUSES[HW_STATUS]}'
    if HW_STATUS in STATUSES.keys():
        return REVIEWING.format(HW_NAME, STATUSES[HW_STATUS])
    else:
        raise ValueError(STATUS_ERROR)


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    PAYLOAD = {'from_date': current_timestamp}
    UrlHeadPayload = dict(url=YAP_URL, headers=HEADERS, params=PAYLOAD)
    response = requests.get(**UrlHeadPayload)
    HW_STATUS = response.json()
    if HW_STATUS.get('error') or HW_STATUS.get('code'):
        error = HW_STATUS.get('error')
        code = HW_STATUS.get('code')
        raise RequestException(f'{error}.код {code}')
    return HW_STATUS


def send_message(message):
    try:
        TG_BOT.send_message(chat_id=CHAT_ID, text=message)
        LOGGER.info('Отправлено сообщение в чат!')

    except Exception as SEND_ERROR:
        SEND_ERROR = 'Во время отправки возникла ошибка!'
        LOGGER.error(SEND_ERROR)
        TG_BOT.send_message(chat_id=CHAT_ID, text=SEND_ERROR)


def main():
    current_timestamp = int(time.time())
    INTERVAL = 5 * 60
    while True:
        try:
            LOGGER.debug('Бот был запущен!')
            response = get_homeworks(current_timestamp)
            homeworks = response['homeworks']
            LOGGER.info('Бот отправил сообщение!')
            for homework in homeworks:
                send_message(parse_homework_status(homework))
            time.sleep(INTERVAL)
        except Exception as e:
            ERROR_MESSAGE = f'Бот упал с ошибкой: {e}!'
            LOGGER.error(ERROR_MESSAGE)
            TG_BOT.send_message(chat_id=CHAT_ID, text=ERROR_MESSAGE)
            time.sleep(5)


if __name__ == '__main__':
    main()
