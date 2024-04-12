import time
import logging

from channels_redis.core import RedisChannelLayer

logger = logging.getLogger(__name__)


class CustomRedisChannelLayer(RedisChannelLayer):
    """Переопределен метод group_send для канального слоя Redis"""
    async def group_send(self, group, message, exclude_channel=None):
        """
        В метод добавлена возможность исключить определенный канал из рассылки.
        Чтобы на фронт при отправке изменения модели, канал,
        в котором было изменение, получил только одно сообщение - ответ от бека,
        без рассылки изменения в группу.
        exclude_channel: имя канала, который нужно исключить их получателей
        """
        assert self.valid_group_name(group), "Group name not valid"
        key = self._group_key(group)
        connection = self.connection(self.consistent_hash(group))
        await connection.zremrangebyscore(
            key, min=0, max=int(time.time()) - self.group_expiry
        )

        # это измененная строка исходного кода
        channel_names = [x.decode("utf8") for x in await connection.zrange(key, 0, -1) if
                         x.decode("utf8") != exclude_channel]

        (
            connection_to_channel_keys,
            channel_keys_to_message,
            channel_keys_to_capacity,
        ) = self._map_channel_keys_to_connection(channel_names, message)

        for connection_index, channel_redis_keys in connection_to_channel_keys.items():
            pipe = connection.pipeline()
            for key in channel_redis_keys:
                pipe.zremrangebyscore(
                    key, min=0, max=int(time.time()) - int(self.expiry)
                )
            await pipe.execute()

            group_send_lua = """
                local over_capacity = 0
                local current_time = ARGV[#ARGV - 1]
                local expiry = ARGV[#ARGV]
                for i=1,#KEYS do
                    if redis.call('ZCOUNT', KEYS[i], '-inf', '+inf') < tonumber(ARGV[i + #KEYS]) then
                        redis.call('ZADD', KEYS[i], current_time, ARGV[i])
                        redis.call('EXPIRE', KEYS[i], expiry)
                    else
                        over_capacity = over_capacity + 1
                    end
                end
                return over_capacity
            """

            args = [
                channel_keys_to_message[channel_key]
                for channel_key in channel_redis_keys
            ]

            args += [
                channel_keys_to_capacity[channel_key]
                for channel_key in channel_redis_keys
            ]

            args += [time.time(), self.expiry]

            connection = self.connection(connection_index)
            channels_over_capacity = await connection.eval(
                group_send_lua, len(channel_redis_keys), *channel_redis_keys, *args
            )
            if channels_over_capacity > 0:
                logger.info(
                    "%s of %s channels over capacity in group %s",
                    channels_over_capacity,
                    len(channel_names),
                    group,
                )
