from random import choice
import requests
from vk_api import Captcha
from vk_api.longpoll import VkLongPoll, VkEventType, CHAT_START_ID
from vk_api.requests_pool import VkRequestsPool
from vk_api.utils import get_random_id
from vk_api.upload import VkUpload
import time
from vk_api.vk_api import VkApi
from config_pil import *
import io
from json_modules import *


def captcha_solve(captcha: Captcha):
    files = {'file': ("captcha.jpg", captcha.get_image(), "image/jpeg")}
    while True:
        req = requests.post("http://rucaptcha.com/in.php", data=dict(
            key=RUCAPTCHA_TOKEN,
            method="post",
            phrase=0,
            regsense=0,
            numeric=4,
            min_len=1,
            max_len=10,
            language=2,
            lang='en',
            textinstructions="Просто пиши буквы как видишь, маленькими буквами",
            json=1
        ), files=files).json()
        if req['request'] != 'ERROR_NO_SLOT_AVAILABLE':
            break
    while True:
        time.sleep(5)
        resp = requests.get("http://rucaptcha.com/res.php", params=dict(
            key=RUCAPTCHA_TOKEN,
            action="get",
            id=req['request'],
            json=1
        )).json()
        if resp['status']:
            return captcha.try_again(resp['request'])
        if resp['request'] == "ERROR_CAPTCHA_UNSOLVABLE":
            return captcha.try_again("")


def standart_captcha_solve(captcha: Captcha):
    url = captcha.get_url()
    print("Ссылка на капчу: ", url)
    key = input("Введите капчу из данной ссылки выше: ")
    return captcha.try_again(key)


def auth_handler():
    key = input("Напишите код безопасности: ")
    remember_device = True
    return key, remember_device


def get_original_photo_url(obj):
    max_size = 0
    url = ""
    for size in obj['sizes']:
        current_size = size['width'] * size['height']
        if current_size > max_size:
            max_size = current_size
            url = size['url']
    return url


config = read_json_from_filename('config.json')
RUCAPTCHA_TOKEN = config["rucaptcha_token"]
COUNT_FORWARD_MESSAGES = config['count_forward_msgs']
ENABLED_FORWARD = config['enable_forward']
COLLISION_ENABLED = config['collision_enable']
change_fontsize(config['fontsize'])
change_font(config['fontfile'])


vk_auth_params = dict(
    **(dict(login=config['login'], password=config['password']) if "token" not in config else dict(token=config["token"])), app_id=2685278, auth_handler=auth_handler,
    captcha_handler=captcha_solve if config['captcha_method_input'] != "standart_input" else standart_captcha_solve
)
vk = VkApi(**vk_auth_params)
if "token" not in config:
    vk.auth()
api = vk.get_api()
upload = VkUpload(vk)
attachments = []
target_chat_id = config['target_chat_id']
req = api.messages.getHistoryAttachments(
    media_type="photo", peer_id=CHAT_START_ID + target_chat_id, count=200)

# Сбор базы гифов
gifs = []
with open('gifs.txt') as f:
    gifs = f.read().split()

# Сбор базы сообщений для данного чата
messages = []
req_mes = api.messages.getHistory(
    peer_id=CHAT_START_ID + target_chat_id, count=0)
messages_pool = []
with VkRequestsPool(vk) as pool:
    for offset in range(0, req_mes['count'], 200):
        messages_pool.append(pool.method("messages.getHistory", dict(
            offset=offset,
            count=200,
            peer_id=CHAT_START_ID + target_chat_id
        )))
for message_pool in messages_pool:
    if message_pool.ok:
        messages.extend(message_pool.result['items'])
    else:
        print(message_pool.error)
# Выбираем только не пустые сообщения
messages = list(filter(lambda x: 0 < len(x['text']) < 500, messages))
# Сбор базы всех фотографий данного чата
for photo in req['items']:
    if "attachment" in photo:
        attachment = photo['attachment']['photo']
        attachments.append([attachment['owner_id'], attachment['id'],
                           attachment['access_key'], get_original_photo_url(attachment)])
while 'next_from' in req:
    req = api.messages.getHistoryAttachments(
        peer_id=CHAT_START_ID + target_chat_id, media_type="photo", count=200, start_from=req['next_from'])
    for photo in req['items']:
        if "attachment" in photo:
            attachment = photo['attachment']['photo']
            attachments.append(
                [attachment['owner_id'], attachment['id'], attachment['access_key'], get_original_photo_url(attachment)])

while True:
    try:
        # Включение в работу бота
        lp = VkLongPoll(vk)
        print("Ready")
        for event in lp.listen():
            # Проверка на то что это сообщение из чата из которой требуется работа бота
            message_is_new = event.type == VkEventType.MESSAGE_NEW
            valid_chat_id = event.chat_id == target_chat_id if event.from_chat else False
            if message_is_new and event.from_chat and valid_chat_id:
                if hasattr(event, 'text'):
                    # Проверка совпадения команды
                    current_text = event.text.lower().strip()
                    if COLLISION_ENABLED:
                        current_text = current_text.replace('p', 'р').replace(
                            'a', 'а').replace('o', 'о')
                    text_valid = "рандом" in current_text
                    if text_valid:
                        # Выбор рандомной картинки
                        rnd_attach = choice(attachments)
                        req = api.photos.getById
                        tmp_attach_file = requests.get(rnd_attach[3], stream=True).raw
                        img = Image.open(tmp_attach_file)
                        texts = []
                        from_ids = []
                        msg_ids = []
                        text_for_print = ""
                        # Выбор некоторого количества рандомных сообщений
                        for i in range(COUNT_FORWARD_MESSAGES):
                            msg = choice(messages)
                            msg_ids.append(msg["id"])
                            texts.append(msg['text'])
                            from_ids.append(msg['from_id'])
                        users = api.users.get(user_ids=list(set(from_ids)))
                        for i in range(len(from_ids)):
                            for user in users:
                                if user['id'] == from_ids[i]:
                                    texts[i] =  f"{user['first_name']} {user['last_name']}: {texts[i]}"
                                    break
                        for i in texts:
                            text_for_print += i + '\n'
                        # Создаем мем
                        img_main = get_meme(text_for_print, img)
                        file = io.BytesIO()
                        img_main.save(file, format="PNG")
                        file.seek(0)
                        obj = upload.photo_messages(
                            file, CHAT_START_ID + target_chat_id)
                        vk_photo_url = 'photo{}_{}_{}'.format(
                            obj[0]['owner_id'], obj[0]['id'], obj[0]['access_key']
                        )
                        # Отправляем в чат
                        api.messages.send(chat_id=event.chat_id, message="&#8291;", attachment=vk_photo_url,
                                        forward_messages=msg_ids if ENABLED_FORWARD else [], random_id=get_random_id())
                        continue
                    if COLLISION_ENABLED:
                        current_text = current_text.replace(
                            'a', 'а').replace('p', 'р')
                    text_valid = "бэбра" in current_text
                    if text_valid:
                        api.messages.send(chat_id=event.chat_id, message="&#8291;", attachment=choice(gifs),
                                        random_id=get_random_id())
                        continue
    except:
        import time
        time.sleep(1)