import logging
from collections import defaultdict, namedtuple
from pathlib import Path
from typing import Dict, List

from telethon import TelegramClient, events, Button, errors

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)
LOGGER = logging.getLogger('channel_bot')

TOKEN_FILE = Path(__file__).absolute().parent / 'token'
api_token, bot_token = TOKEN_FILE.read_text().splitlines()
api_id, api_hash = api_token.split(':')
client = TelegramClient('LuzinChannelBot', api_id, api_hash).start(bot_token=bot_token)
LOGGER.info('Client is created, bot is started.')

ChannelInfo = namedtuple('ChannelInfo', ['name', 'id'])
TECH_PHYS_MATH_TEMPLE_CHANNEL_INFO = ChannelInfo(name='Rainbow TechPhysMath Temple', id=-1002063345022)

Proposal = namedtuple('Proposal', ['text', 'hashtag', 'which'])
PROPOSALS = {
    b'QUESTION': Proposal(text='Вопрос', hashtag='#вопрос', which='которым'),
    b'PROBLEM': Proposal(text='Задачу', hashtag='#задача', which='которой'),
    b'INTERESTING': Proposal(text='Интересный пост', hashtag='#интересное', which='которым'),
}

Topic = namedtuple('Topic', ['text', 'hashtag', 'adpositional'])
TOPICS = {
    b'MATH': Topic(text='Математика', hashtag='#математика', adpositional=' по математике'),
    b'CS': Topic(text='Информатика\n(CS)', hashtag='#информатика', adpositional=' по информатике'),
    b'ELEC': Topic(text='Электроника', hashtag='#электроника', adpositional=' по электронике'),
    b'OTHER': Topic(text='Другое', hashtag='#другое', adpositional=''),
}

START_MESSAGE = {
    'message': 'Что вы хотите предложить в канал:',
    'buttons': [Button.inline(text=proposal.text, data=data) for data, proposal in PROPOSALS.items()]
}

CANCEL_BUTTON_DATA = b'CANCEL'
CANCEL_BUTTON = Button.inline(text='Отмена', data=CANCEL_BUTTON_DATA)

client_table: Dict[int, List[namedtuple]] = defaultdict(list)


def _get_text_for_channel(username: str, message_text: str, sender_id: int) -> str:
    proposal, topic = client_table[sender_id]
    lines = (
        f'Предложено @{username}',
        message_text,
        f'{proposal.hashtag} {topic.hashtag}'
    )
    return '\n'.join(lines)


@client.on(events.NewMessage())
async def my_event_handler(event):
    sender = await event.get_sender()
    sender_id = event.sender_id
    client_stack_len: int = len(client_table[sender_id])
    message = event.message
    try:
        if client_stack_len == 0 and message.text == '/start':
            await client.send_message(entity=sender_id, **START_MESSAGE)
        elif client_stack_len == 2:
            message.text = _get_text_for_channel(sender.username, message.text, sender_id)
            client_table.pop(sender_id)
            await client.send_message(entity=TECH_PHYS_MATH_TEMPLE_CHANNEL_INFO.id, message=message)
            # NOTE: debug
            # await client.send_message(entity=sender_id, message=message)
        else:
            await client.delete_messages(entity=event.chat_id, message_ids=event.message.id)
    except errors.RPCError as er:
        client_table[sender_id] = []
        await client.send_message(entity=sender_id, message=f'Error: {er.message}\nПопробуйте снова.')


def _pairs_generator(container):
    pair = []
    for item in container:
        pair.append(item)
        if len(pair) == 2:
            yield pair
            pair = []
    if pair:
        yield pair


@client.on(events.CallbackQuery())
async def callback(event):
    sender_id: int = event.sender_id
    if event.data == CANCEL_BUTTON_DATA:
        client_table[sender_id] = []
        await event.edit(START_MESSAGE['message'], buttons=START_MESSAGE['buttons'])
    elif event.data in PROPOSALS:
        client_table[sender_id] = [PROPOSALS[event.data]]
        buttons = [Button.inline(text=topic.text, data=key) for key, topic in TOPICS.items()]
        buttons.append(CANCEL_BUTTON)
        await event.edit('Выберите тему: ', buttons=list(_pairs_generator(buttons)))
    elif event.data in TOPICS:
        if len(client_table[sender_id]) != 1:
            await event.edit(START_MESSAGE['message'], buttons=START_MESSAGE['buttons'])
            return
        client_table[sender_id].append(TOPICS[event.data])
        proposal, topic = client_table[sender_id]
        message = f'Введите {proposal.text.lower()}{topic.adpositional}, {proposal.which} вы хотели поделиться.'
        await event.edit(message, buttons=CANCEL_BUTTON)
    else:
        raise RuntimeError(f'Unknown button data: {event.data}')


client.run_until_disconnected()
