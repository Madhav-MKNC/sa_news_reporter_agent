import os
import json
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel
from typing import List, Dict, Optional

from app.configs import NEWS_DATA_STORE_DIR


class NewsItemModel(BaseModel):
    id: Optional[str] = str(datetime.now().strftime("%I_%M_%p_%d_%m_%Y"))
    headline_str: Optional[str]
    content_str: str
    tags_list: Optional[List[str]] = []
    
    def create_dir(self):
        if not os.path.exists(NEWS_DATA_STORE_DIR):
            os.makedirs(NEWS_DATA_STORE_DIR)
        os.makedirs(os.path.join(NEWS_DATA_STORE_DIR, self.id), exist_ok=True)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'NewsItemModel':
        return cls(
            id=data.get('id', str(datetime.now().strftime("%I_%M_%p_%d_%m_%Y"))),
            headline_str=data.get('headline_str'),
            content_str=data.get('content_str'),
            tags_list=data.get('tags_list', [])
        )

    def to_json(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "headline_str": self.headline_str,
            "content_str": self.content_str,
            "tags_list": " ".join(self.tags_list)
        }

    def save_json(self):
        filepath = os.path.join(NEWS_DATA_STORE_DIR, self.id, "data.json")
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(self.to_json(), file, ensure_ascii=False, indent=4)




