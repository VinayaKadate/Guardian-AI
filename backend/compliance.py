from database import Database
from typing import List, Tuple

class ComplianceChecker:
    def __init__(self, db: Database):
        self.db = db
        self.banned_entities = self.db.get_all_banned_entities()
    
    def refresh_banned_list(self):
        self.banned_entities = self.db.get_all_banned_entities()
    
    def check_text(self, text: str) -> Tuple[bool, str, dict]:
        text_lower = text.lower()
        for entity in self.banned_entities:
            if entity in text_lower:
                info = self.db.get_banned_entity_info(entity)
                return False, entity, info
        return True, None, None
    
    def check_documents(self, docs: List[str]) -> Tuple[bool, str, dict]:
        for doc in docs:
            is_compliant, entity, info = self.check_text(doc)
            if not is_compliant:
                return False, entity, info
        return True, None, None