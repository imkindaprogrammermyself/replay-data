# coding=utf-8
import json
import logging
import os
import requests
from json import JSONEncoder

from replay_unpack.clients import wot, wows
from replay_unpack.replay_reader import ReplayReader, ReplayInfo

logging.basicConfig(level=logging.ERROR)

class ReplayParser(object):
    def __init__(self, replay_path, strict: bool = False):
        self._replay_path = replay_path
        self._is_strict_mode = strict
        self._reader = ReplayReader(replay_path)

    def get_info(self):
        replay = self._reader.get_replay_data()

        error = None
        try:
            hidden_data = self._get_hidden_data(replay)
        except Exception as e:
            if isinstance(e, RuntimeError):
                error = str(e)
            logging.exception(e)
            hidden_data = None

            # raise error in strict mode
            if self._is_strict_mode:
                raise

        return dict(
            open=replay.engine_data,
            extra_data=replay.extra_data,
            hidden=hidden_data,
            error=error
        )

    def _get_hidden_data(self, replay: ReplayInfo):
        player = wows.ReplayPlayer(replay.engine_data
                                   .get('clientVersionFromXml')
                                   .replace(' ', '')
                                   .split(','))

        player.play(replay.decrypted_data, self._is_strict_mode)
        return player.get_info()

# def prettify_keys(o: object):
#     temp = {}
#     for k, v in o.__dict__.items():
#         a = k.split("_")
#         if len(a) > 0:
#             c = [a[0]]
#             for b in a[1:]:
#                 c.append(f"{b[0].upper()}{b[1:]}")
#             temp["".join(c)] = v
#         else:
#             temp[k] = v
#     return temp
#
#
# if __name__ == '__main__':
#     download_url = f"https://replayswows.com/replay/download/{134108}"
#
#     response = requests.get(download_url)
#
#     if response.status_code == 200:
#         replay_info = ReplayParser(response.content).get_info()
#
#         print(json.dumps(replay_info['hidden']['extracted_data'], indent=1,
#                          default=prettify_keys))
