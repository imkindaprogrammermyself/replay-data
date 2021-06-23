class Message:
    def __init__(self):
        self.sender_account_id: int = 0
        self.sender_name: str = ""
        self.sender_clan_name: str = ""
        self.sender_is_ally: bool = False
        self.message_type: str = ""
        self.message_content: str = ""
        self.message_game_time: int = 0