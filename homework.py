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
logger = logging.getLogger(__name__)

PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
if PRAKTIKUM_TOKEN is None:
    logger.error('Токен YAP отсутсвует!')
    raise ValueError('Токен YAP отсутсвует!')

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
if TELEGRAM_TOKEN is None:
    logger.error('Токен TG отсутсвует!')
    raise ValueError('Токен TG отсутсвует!')

CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
if CHAT_ID is None:
    logger.error('Токен CHAT отсутсвует!')
    raise ValueError('Токен CHAT отсутсвует!')

TG_BOT = telegram.Bot(token=TELEGRAM_TOKEN)
YAP_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
AUTH_YAP_TOKEN = f'OAuth {PRAKTIKUM_TOKEN}'


STATUS_ERROR = 'Ошибка статуса!'
NONE_ERROR = 'STATUS OR HOMEWORK IS NONE'

stauses = {
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, работа зачтена!',
    'reviewing': 'Вашу работу проверяют.',
}


def parse_homework_status(homework):
    hw_name = homework.get('homework_name')
    hw_status = homework.get('status')

    if hw_name is None or hw_status is None:
        logger.error(NONE_ERROR)
        raise ValueError(NONE_ERROR)

    reviewing = f'У вас проверили работу "{hw_name}"!\n\n{stauses[hw_status]}'
    if hw_status in stauses.keys():
        return reviewing.format(hw_name, stauses[hw_status])
    else:
        logger.error(STATUS_ERROR)
        raise ValueError(STATUS_ERROR)


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())

    headers = {'Authorization': AUTH_YAP_TOKEN}
    payload = {'from_date': current_timestamp}
    UrlHeadPayload = dict(url=YAP_URL, headers=headers, params=payload)
    try:
        response = requests.get(**UrlHeadPayload)
    except RequestException as error_requests:
        URL_ERROR = (f'Во время запроса {YAP_URL}'
                     f'произошла ошибка {error_requests}!')
        logger.error(URL_ERROR)
    hw_status = response.json()
    if hw_status.get('error') or hw_status.get('code'):
        error = hw_status.get('error')
        code = hw_status.get('code')
        raise RequestException(f'{error}.код {code}')
    return hw_status


def send_message(message):
    try:
        TG_BOT.send_message(chat_id=CHAT_ID, text=message)
        logger.info('Отправлено сообщение в чат!')
    except Exception as SEND_ERROR:
        SEND_ERROR = 'Во время отправки возникла ошибка!'
        logger.error(SEND_ERROR)
        TG_BOT.send_message(chat_id=CHAT_ID, text=SEND_ERROR)


def main():
    current_timestamp = int(time.time())
    INTERVAL = 5 * 60
    while True:
        try:
            logger.debug('Бот был запущен!')
            response = get_homeworks(current_timestamp)
            homeworks = response['homeworks']
            logger.info('Бот отправил сообщение!')
            for homework in homeworks:
                send_message(parse_homework_status(homework))
            time.sleep(INTERVAL)
        except Exception as e:
            ERROR_MESSAGE = f'Бот упал с ошибкой: {e}!'
            logger.error(ERROR_MESSAGE)
            TG_BOT.send_message(chat_id=CHAT_ID, text=ERROR_MESSAGE)
            time.sleep(5)


if __name__ == '__main__':
    main()
