# coding=utf-8
import logging
import pickle
import math

from replay_unpack.core import IBattleController
from replay_unpack.core.entity import Entity
from .constants import DamageStatsType, Category, TaskType, Status
from replay_data import *

try:
    from .constants import DEATH_TYPES
except ImportError:
    DEATH_TYPES = {}
from .players_info import PlayersInfo


class BattleController(IBattleController):

    def __init__(self):
        self._entities = {}
        self._achievements = {}
        self._ribbons = {}
        self._players = PlayersInfo()
        self._battle_result = None
        self._damage_map = {}
        self._shots_damage_map = {}
        self._death_map = []
        self._map = {}
        self._player_id = None
        self._arena_id = None
        self._dead_planes = {}

        ################################################################################################################
        self._time_left = 0
        self._match = Match()
        self._players_data: dict[int, Player] = {}
        self._players_data_vid: dict[int, Player] = {}
        self._message_data: list[Message] = []
        self._distances_data: dict[int, Distance] = {}
        self._owner_x = -2500.0
        self._owner_y = -2500.0
        ################################################################################################################

        Entity.subscribe_method_call('Avatar', 'onBattleEnd', self.onBattleEnd)
        Entity.subscribe_method_call('Avatar', 'onArenaStateReceived', self.onArenaStateReceived)
        Entity.subscribe_method_call('Avatar', 'onGameRoomStateChanged', self.onPlayerInfoUpdate)
        Entity.subscribe_method_call('Avatar', 'receiveVehicleDeath', self.receiveVehicleDeath)
        # Entity.subscribe_method_call('Vehicle', 'setConsumables', self.onSetConsumable)
        Entity.subscribe_method_call('Avatar', 'onRibbon', self.onRibbon)
        Entity.subscribe_method_call('Avatar', 'onAchievementEarned', self.onAchievementEarned)
        Entity.subscribe_method_call('Avatar', 'receiveDamageStat', self.receiveDamageStat)
        Entity.subscribe_method_call('Avatar', 'receive_planeDeath', self.receive_planeDeath)
        Entity.subscribe_method_call('Avatar', 'onNewPlayerSpawnedInBattle', self.onNewPlayerSpawnedInBattle)

        Entity.subscribe_method_call('Vehicle', 'receiveDamagesOnShip', self.g_receiveDamagesOnShip)

        ################################################################################################################

        Entity.subscribe_property_change('BattleLogic', 'timeLeft', self.on_time_left_change)
        Entity.subscribe_method_call('Avatar', 'onChatMessage', self.on_chat_message)
        Entity.subscribe_method_call('Avatar', 'updateMinimapVisionInfo', self.updateMinimapVisionInfo)

    def on_time_left_change(self, avatar, time_left):
        self._time_left = time_left

    def create_player_data(self):
        owner: dict = list(
            filter(lambda ply: ply["avatarId"] == self._player_id, self._players.get_info().values())).pop()

        self._match.realm = owner["realm"]
        self._match.player_avatar_id = owner["avatarId"]
        self._match.player_vehicle_id = owner["shipId"]
        self._match.player_team = owner["teamId"]

        for p in self._players.get_info().values():
            player = Player()
            player.name = p["name"]
            player.player_account_id = p["accountDBID"]
            player.avatar_id = p["avatarId"]
            player.vehicle_id = p["shipId"]
            player.ship_params_id = p["shipParamsId"]
            player.clan_id = p["clanID"]
            player.clan_tag = p["clanTag"]
            player.clan_color = p["clanColor"]
            player.is_ally = self._match.player_team == p["teamId"]
            self._players_data[player.avatar_id] = player
            self._players_data_vid[player.vehicle_id] = player

    def on_chat_message(self, avatar, avatar_id: int, group: str, message_content: str, *args):
        player = self._players_data[avatar_id]
        message = Message()
        message.sender_account_id = player.player_account_id
        message.sender_name = player.name
        message.sender_clan_name = player.clan_tag
        message.sender_is_ally = player.is_ally
        message.message_type = group
        message.message_content = message_content
        message.message_game_time = self._time_left

        self._message_data.append(message)

    def updateMinimapVisionInfo(self, avatar, ships_minimap_diff, buildings_minimap_diff):
        pack_pattern = (
            (-2500.0, 2500.0, 11),
            (-2500.0, 2500.0, 11),
            (-3.141592753589793, 3.141592753589793, 8)
        )
        for e in ships_minimap_diff:
            try:
                vehicle_id = e['vehicleID']
                x, y, yaw = unpack_values(e['packedData'], pack_pattern)

                if vehicle_id == self._match.player_vehicle_id:
                    self._owner_x = x
                    self._owner_y = y

                if x != -2500.0 and y != - 2500.0 and self._owner_x != -2500.0 and self._owner_y != -2500.0 \
                        and self._match.player_vehicle_id != vehicle_id:
                    player = self._players_data_vid[vehicle_id]
                    dist = math.hypot(self._owner_x - x, self._owner_y - y) * 0.03
                    if vehicle_id not in self._distances_data:
                        distance = Distance()
                        distance.avatar_id = player.avatar_id
                        distance.vehicle_id = player.vehicle_id
                        distance.name = player.name
                        distance.is_ally = player.is_ally
                        distance.distances_over_time[self._time_left] = round(dist, 1)
                        self._distances_data[vehicle_id] = distance
                    else:
                        self._distances_data[vehicle_id].distances_over_time[self._time_left] = round(dist, 1)
            except KeyError:
                pass

    ####################################################################################################################

    def onSetConsumable(self, vehicle, blob):
        print(pickle.loads(blob))

    @property
    def entities(self):
        return self._entities

    @property
    def battle_logic(self):
        return next(e for e in self._entities.values() if e.get_name() == 'BattleLogic')

    def create_entity(self, entity: Entity):
        self._entities[entity.id] = entity

    def destroy_entity(self, entity: Entity):
        self._entities.pop(entity.id)

    def on_player_enter_world(self, entity_id: int):
        self._player_id = entity_id

    def get_info(self):
        return dict(
            extracted_data=dict(match_data=self._match, players_data=self._players_data,
                                message_data=self._message_data, distances_data=self._distances_data),
            achievements=self._achievements,
            ribbons=self._ribbons,
            players=self._players.get_info(),
            battle_result=self._battle_result,
            damage_map=self._damage_map,
            shots_damage_map=self._shots_damage_map,
            death_map=self._death_map,
            death_info=self._getDeathsInfo(),
            map=self._map,
            player_id=self._player_id,
            control_points=self._getCapturePointsInfo(),
            tasks=list(self._getTasksInfo()),
            skills=dict(),
            # planes are only updated in AOI
            # so information is not right
            # planes=self._dead_planes,
            arena_id=self._arena_id
        )

    def _getDeathsInfo(self):
        deaths = {}
        for killedVehicleId, fraggerVehicleId, typeDeath in self._death_map:
            death_type = DEATH_TYPES.get(typeDeath)
            if death_type is None:
                logging.warning('Unknown death type %s', typeDeath)
                continue

            deaths[killedVehicleId] = {
                'killer_id': fraggerVehicleId,
                'icon': death_type['icon'],
                'name': death_type['name'],
            }
        return deaths

    def _getCapturePointsInfo(self):
        return self.battle_logic.properties['client']['state'].get('controlPoints', [])

    def _getTasksInfo(self):
        tasks = self.battle_logic.properties['client']['state'].get('tasks', [])
        for task in tasks:
            yield {
                "category": Category.names[task['category']],
                "status": Status.names[task['status']],
                "name": task['name'],
                "type": TaskType.names[task['type']]
            }

    def onBattleEnd(self, avatar, teamId, state):
        self._battle_result = dict(
            winner_team_id=teamId,
            victory_type=state
        )

    def onNewPlayerSpawnedInBattle(self, avatar, pickle_data):
        self._players.create_or_update_players(
            pickle.loads(pickle_data))

    def onArenaStateReceived(self, avatar, arenaUniqueId, teamBuildTypeId, preBattlesInfo, playersStates,
                             observersState, buildingsInfo):
        self._arena_id = arenaUniqueId
        self._players.create_or_update_players(
            pickle.loads(playersStates))
        self.create_player_data()

    def onPlayerInfoUpdate(self, avatar, playersData, observersData):
        self._players.create_or_update_players(
            pickle.loads(playersData))

    def receiveDamageStat(self, avatar, blob):
        normalized = {}
        for (type_, bool_), value in pickle.loads(blob).items():
            # TODO: improve damage_map and list other damage types too
            if bool_ != DamageStatsType.DAMAGE_STATS_ENEMY:
                continue
            normalized.setdefault(type_, {}).setdefault(bool_, 0)
            normalized[type_][bool_] = value
        self._damage_map.update(normalized)

    def onRibbon(self, avatar, ribbon_id):
        self._ribbons.setdefault(avatar.id, {}).setdefault(ribbon_id, 0)
        self._ribbons[avatar.id][ribbon_id] += 1

    def onAchievementEarned(self, avatar, avatar_id, achievement_id):
        self._achievements.setdefault(avatar_id, {}).setdefault(achievement_id, 0)
        self._achievements[avatar_id][achievement_id] += 1

    def receiveVehicleDeath(self, avatar, killedVehicleId, fraggerVehicleId, typeDeath):
        self._death_map.append((killedVehicleId, fraggerVehicleId, typeDeath))

    def g_receiveDamagesOnShip(self, vehicle, damages):
        for damage_info in damages:
            self._shots_damage_map.setdefault(vehicle.id, {}).setdefault(damage_info['vehicleID'], 0)
            self._shots_damage_map[vehicle.id][damage_info['vehicleID']] += damage_info['damage']

    def receive_planeDeath(self, avatar, squadronID, planeIDs, reason, attackerId):
        self._dead_planes.setdefault(attackerId, 0)
        self._dead_planes[attackerId] += len(planeIDs)

    @property
    def map(self):
        raise NotImplemented()

    @map.setter
    def map(self, value):
        self._map = value.lstrip('spaces/')


def unpack_value(packed_value, value_min, value_max, bits):
    return packed_value / (2 ** bits - 1) * (abs(value_min) + abs(value_max)) - abs(value_min)


def unpack_values(packed_value, pack_pattern):
    values = []
    for i, pattern in enumerate(pack_pattern):
        min_value, max_value, bits = pattern
        value = packed_value & (2 ** bits - 1)

        values.append(unpack_value(value, min_value, max_value, bits))
        packed_value = packed_value >> bits
    try:
        assert packed_value == 0
    except AssertionError:
        pass
    return tuple(values)
