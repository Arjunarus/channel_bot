import asyncio
import logging
import os
from collections import defaultdict
from telethon import TelegramClient, events, Button

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token')
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.DEBUG)

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
    message = event.message.to_dict()['message']
    if taglen == 0 and message == '/start':
        await client.send_message(entity=sender_id, **ENTRY_POINT)
    elif taglen == 2:
        post = f'Предложил {sender.first_name} {sender.last_name}\n' \
               f'{message}\n' \
               f'{" ".join(client_table[sender_id])}'
        client_table.pop(sender_id)
        await client.send_message(entity=TEMPLE_CHANNEL_ID, message=post)
    else:
        await client.delete_messages(entity=event.chat_id, message_ids=event.message.id)


@client.on(events.CallbackQuery())
async def callback(event):
    sender_id = event.sender_id
    if event.data in HASHTAGS:
        client_table[sender_id].append(HASHTAGS[event.data])

    if event.data in [b'post', b'cancel']:
        client_table[sender_id] = []
        await event.edit(ENTRY_POINT['message'], buttons=ENTRY_POINT['buttons'])
    elif event.data in [b'question', b'problem', b'interesting']:
        await event.edit('Выберите тему: ', buttons=[
            [
                Button.inline(text='Математика', data='math'),
                Button.inline(text='Информатика (CS)', data='cs'),
                Button.inline(text='Электроника', data='elec')
            ],
            [
                Button.inline(text='Другое', data='other'),
                Button.inline(text='Отмена', data='cancel')
            ]
        ])
    else:
        await event.edit('Введите ваше сообщение для канала', buttons=Button.inline(text='Отмена', data='cancel'))


client.run_until_disconnected()
