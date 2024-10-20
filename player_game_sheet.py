class PlayerGameSheet:
    def __init__(self, game_id, player_id, goals, assists, points, plus_minus, pim, sog, hits, ppg, toi, face_off_percentage, team_id, player_blocked_shots):
        self.game_id = game_id
        self.player_id = player_id
        self.goals = goals
        self.assists = assists
        self.points = points
        self.plus_minus = plus_minus
        self.pim = pim
        self.sog = sog
        self.hits = hits
        self.ppg = ppg
        self.toi = toi
        self.face_off_percentage = face_off_percentage
        self.team_id = team_id
        self.player_blocked_shots = player_blocked_shots
