import sqlite3
from typing import List, Set

class Database:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_entities (
                entity TEXT PRIMARY KEY,
                source_file TEXT,
                sheet_name TEXT,
                row_number INTEGER
            )
        """)
        conn.commit()
        conn.close()
    
    def add_banned_entities(self, entities: List[dict]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for entity in entities:
            cursor.execute("""
                INSERT OR REPLACE INTO banned_entities 
                (entity, source_file, sheet_name, row_number)
                VALUES (?, ?, ?, ?)
            """, (entity['entity'].lower(), entity['source_file'], 
                  entity['sheet_name'], entity['row_number']))
        conn.commit()
        conn.close()
    
    def get_all_banned_entities(self) -> Set[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT entity FROM banned_entities")
        entities = {row[0] for row in cursor.fetchall()}
        conn.close()
        return entities
    
    def get_banned_entity_info(self, entity: str) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT source_file, sheet_name, row_number 
            FROM banned_entities WHERE entity = ?
        """, (entity.lower(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'source_file': row[0],
                'sheet_name': row[1],
                'row_number': row[2]
            }
        return None