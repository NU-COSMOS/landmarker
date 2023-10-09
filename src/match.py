from typing import List, Dict
import datetime

class Match:
    def __init__(self, 
                team: str, 
                match_name: str, 
                map_name: str, 
                date: datetime.date, 
                rcount: int,
                pts: List[Dict[str, float]])->None:
        """
        Args:
            team (str): チーム名
            match_name (str): スクリム(orリーグ)名
            map_name (str): マップ名
            date (datetime.date): 試合の日付
            rcount (int): ラウンド数
            pts (List[Dict[str, float]]): 降下地点のリスト [{x:x座標, y:y座標}, ]
        """
        self.team = team
        self.match_name = match_name
        self.map_name = map_name
        self.date = date
        self.rcount = rcount
        self.pts = pts