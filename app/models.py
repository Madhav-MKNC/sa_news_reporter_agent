import os
import json
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel
from typing import List, Dict, Optional

from app.configs import NEWS_DATA_STORE_DIR


class NewsItemModel(BaseModel):
    id: Optional[str] = f"{str(datetime.now().strftime("%I_%M_%p_%d_%m_%Y"))}_{str(uuid4())}"
    headline_str: Optional[str]
    content_str: str
    tags_list: Optional[List[str]] = []
    source_list: Optional[List[str]] = []
    timestamp_str: str
    
    def create_dir(self):
        if not os.path.exists(NEWS_DATA_STORE_DIR):
            os.makedirs(NEWS_DATA_STORE_DIR)
        os.makedirs(os.path.join(NEWS_DATA_STORE_DIR, self.id), exist_ok=True)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'NewsItemModel':
        return cls(
            id=data.get('id', f"{str(datetime.now().strftime("%I_%M_%p_%d_%m_%Y"))}_{str(uuid4())}"),
            headline_str=data.get('headline_str'),
            content_str=data.get('content_str'),
            tags_list=data.get('tags_list', []),
            source_list=data.get('source_list', []),
            timestamp_str=data.get('timestamp_str', datetime.now().isoformat())
        )

    def to_json(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "headline_str": self.headline_str,
            "content_str": self.content_str,
            "tags_list": self.tags_list,
            "source_list": self.source_list,
            "timestamp_str": self.timestamp_str
        }

    def save_json(self):
        filepath = os.path.join(NEWS_DATA_STORE_DIR, self.id, "data.json")
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(self.to_json(), file, ensure_ascii=False, indent=4)




