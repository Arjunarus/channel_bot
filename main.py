import asyncio
import logging
import os
from collections import defaultdict
from telethon import TelegramClient, events, Button, errors

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token')
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

with open(TOKEN_FILE, 'r') as tokenfile:
    api_id, api_hash = tokenfile.readline().strip().split(':')
    bot_token = tokenfile.readline().strip()

client = TelegramClient('LuzinChannelBot', api_id, api_hash).start(bot_token=bot_token)

HASHTAGS = {
    b'question': '#вопрос',
    b'problem': '#задача',
    b'interesting': '#интересное',
    b'math': '#математика',
    b'cs': '#информатика',
    b'elec': '#электроника',
    b'other': '#другое'
}

ENTRY_POINT = {
    'message': 'Что вы хотите предложить в канал:',
    'buttons': [
        Button.inline(text='Вопрос', data='question'),
        Button.inline(text='Задачу', data='problem'),
        Button.inline(text='Интересное', data='interesting')
    ]
}
TEMPLE_CHANNEL_NAME = 'Rainbow TechPhysMath Temple'
TEMPLE_CHANNEL_ID = -1002063345022
client_table = defaultdict(list)


@client.on(events.NewMessage())
async def my_event_handler(event):
    sender = await event.get_sender()
    sender_id = event.sender_id
    taglen = len(client_table[sender_id])
    message = event.message
    message_text = message.text
    try:
        if taglen == 0 and message_text == '/start':
            await client.send_message(entity=sender_id, **ENTRY_POINT)
        elif taglen == 2:
            post = f'Предложено @{sender.username}\n' \
                   f'{message_text}\n' \
                   f'{" ".join(HASHTAGS.get(dat, "") for dat in client_table[sender_id])}'
            client_table.pop(sender_id)
            message.text = post
            await client.send_message(entity=TEMPLE_CHANNEL_ID, message=post)
            # NOTE: For debugging
            # await client.send_message(entity=sender_id, message=message)
        else:
            await client.delete_messages(entity=event.chat_id, message_ids=event.message.id)
    except errors.RPCError as er:
        client_table[sender_id] = []
        await client.send_message(entity=sender_id, message=f'Error: {er.message}\nПопробуйте снова.')


def get_invite_message(sender_id):
    flavors = set(client_table[sender_id])
    kind = list(flavors.intersection({b'question', b'problem', b'interesting'}))[0]
    kind_txt = {
        b'question': 'ваш вопрос',
        b'problem': 'вашу задачу',
        b'interesting': 'интересный пост'
    }[kind]
    ending = {
        b'question': 'ым',
        b'problem': 'ой',
        b'interesting': 'ым'
    }[kind]
    topic = {
        b'math': ' по математике',
        b'cs': ' по информатике',
        b'elec': ' по электронике',
        b'other': ''
    }[list(flavors.intersection({b'math', b'cs', b'elec', b'other'}))[0]]

    return f'Введите {kind_txt}{topic}, котор{ending} вы хотели поделиться.'


@client.on(events.CallbackQuery())
async def callback(event):
    sender_id = event.sender_id
    client_table[sender_id].append(event.data)

    if event.data == b'cancel':
        client_table[sender_id] = []
        await event.edit(ENTRY_POINT['message'], buttons=ENTRY_POINT['buttons'])
    elif event.data in [b'question', b'problem', b'interesting']:
        await event.edit('Выберите тему: ', buttons=[
            [
                Button.inline(text='Математика', data='math'),
                Button.inline(text='Электроника', data='elec')
            ],
            [
                Button.inline(text='Информатика (CS)', data='cs')
            ],
            [
                Button.inline(text='Другое', data='other'),
                Button.inline(text='Отмена', data='cancel')
            ]
        ])
    else:
        await event.edit(get_invite_message(sender_id), buttons=Button.inline(text='Отмена', data='cancel'))


client.run_until_disconnected()
