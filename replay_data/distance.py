class Distance:
    def __init__(self):
        self.avatar_id: int = 0
        self.vehicle_id: int = 0
        self.name: str = ""
        self.distances_over_time: dict[int, float] = {}
        self.is_ally: bool = False
