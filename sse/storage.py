import os
import json
import redis

from django_eventstream.storage import StorageBase, EventDoesNotExist
from django_eventstream.event import Event

EVENT_TIMEOUT = 60 * 24


class RedisStorage(StorageBase):
    def __init__(self):
        self.redis_conn = redis.StrictRedis(host=f'{os.getenv("REDIS_HOST")}', port=6379, db=1)

    def append_event(self, channel, event_type, data):
        current_id = self.get_current_id(channel)
        event_id = current_id + 1

        event = Event(
            channel=channel,
            type=event_type,
            data=data,
            id=event_id,
        )

        self.redis_conn.setex(
            f'{channel}-{event_id}',
            EVENT_TIMEOUT,
            self.to_json(event)
        )
        self.redis_conn.set(f'{channel}_id', event_id)

        return event

    def get_events(self, channel, last_id, limit=100):
        events = []
        cur_id = self.get_current_id(channel)

        if cur_id == last_id:
            return []

        if not self.redis_conn.get(f'{channel}-{last_id}'):
            raise EventDoesNotExist(
                'No such event %d' % last_id,
                cur_id)

        for i in range(limit):
            event = self.redis_conn.get(f'{channel}-{last_id+i}')
            if event is None:
                break
            events.append(self.from_bytes_to_event(event))

        if len(events) == 0 or events[0].id != last_id:
            raise EventDoesNotExist(
                'No such event %d' % last_id,
                cur_id)

        return events[1:]

    def get_current_id(self, channel: str):
        if not self.redis_conn.exists(f'{channel}_id'):
            self.redis_conn.set(f'{channel}_id', 0)

        id_key = int(self.redis_conn.get(f'{channel}_id').decode())

        return id_key

    def to_json(self, event: Event):
        return json.dumps({
            'channel': event.channel,
            'type': event.type,
            'data': event.data,
            'id': event.id
        })

    def from_bytes_to_event(self, b_str: bytes):
        event_str = b_str.decode()
        event_dict = json.loads(event_str)
        event = Event(
            channel=event_dict['channel'],
            type=event_dict['type'],
            data=event_dict['data'],
            id=event_dict['id'],
        )
        return event
