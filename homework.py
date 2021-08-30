import logging
import os
import time

import requests
from requests import RequestException
import telegram
from dotenv import load_dotenv

load_dotenv()
os.path.expanduser('~')

PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

TG_BOT = telegram.Bot(token=TELEGRAM_TOKEN)

YAP_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
AUTH_YAP_TOKEN = f'OAuth {PRAKTIKUM_TOKEN}'

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
logger = logging.getLogger(__name__)


def parse_homework_status(homework):
    HW_NAME = homework.get('homework_name')
    HW_STATUS = homework.get('status')
    GOOD_VERDICT = 'Ревьюеру всё понравилось, работа зачтена!'
    BAD_VERDICT = 'К сожалению, в работе нашлись ошибки.'
    REWIEW_VERDICT = 'Вашу работу проверили.'
    STATUS_ERROR = 'Ошибка статуса!'
    STATUSES = {
        'rejected': BAD_VERDICT,
        'approved': GOOD_VERDICT,
        'reviewing': REWIEW_VERDICT,
    }
    REWIEWING = f'У вас проверили работу "{HW_NAME}"!\n\n{STATUSES[HW_STATUS]}'
    if HW_STATUS in STATUSES.keys():
        return REWIEWING.format(HW_NAME, STATUSES[HW_STATUS])
    else:
        return logging.error(STATUS_ERROR)
        return STATUS_ERROR


def get_homeworks(current_timestamp):
    headers = {'Authorization': AUTH_YAP_TOKEN}
    payload = {'from_date': current_timestamp}
    UrlHeadersParams = dict(url=YAP_URL, headers=headers, params=payload)
    response = requests.get(**UrlHeadersParams)
    HW_STATUS = response.json()
    if HW_STATUS.get('error') or HW_STATUS.get('code'):
        ERROR = HW_STATUS.get('error')
        CODE = HW_STATUS.get('code')
        raise RequestException(f'{ERROR}.код {CODE}')
    return HW_STATUS


def send_message(message):
    try:
        TG_BOT.send_message(chat_id=CHAT_ID, text=message)
        logging.info('Отправлено сообщение в чат!')
    except Exception as SEND_ERROR:
        SEND_ERROR = 'Во время отправки возникла ошибка!'
        logger.error(SEND_ERROR)
        TG_BOT.send_message(chat_id=CHAT_ID, text=SEND_ERROR)


def main():
    current_timestamp = int(time.time())
    interval = time.sleep(5 * 60)
    sleep = time.sleep(5)
    while True:
        try:
            logger.debug('Бот был запущен!')
            response = get_homeworks(current_timestamp)
            homeworks = response['homeworks']
            logger.info('Бот отправил сообщение!')
            for homework in homeworks:
                send_message(parse_homework_status(homework))
            interval
        except Exception as e:
            error_message = f'Бот упал с ошибкой: {e}!'
            logger.error(error_message)
            TG_BOT.send_message(chat_id=CHAT_ID, text=error_message)
            sleep


if __name__ == '__main__':
    main()
