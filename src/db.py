import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path
from src.constants import RESULTS_TABLE, RESULTS_SCHEMA

load_dotenv()

class Database:
    def __init__(self):
        self.db_path = Path(os.getenv("DB_PATH"))
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        columns = ", ".join(f"{k} {v}" for k, v in RESULTS_SCHEMA.items())
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {RESULTS_TABLE} ({columns})")
        conn.commit()
        conn.close()

    def save_results(self, results):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for endpoint, data in results.items():
            cursor.execute(
                f"INSERT INTO {RESULTS_TABLE} (endpoint, hop_count, avg_rtt_ms, max_rtt_ms, min_rtt_ms, success_rate, packet_loss) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (endpoint, data["hop_count"], data["avg_rtt_ms"], data["max_rtt_ms"], data["min_rtt_ms"], data["success_rate"], data["packet_loss"])
            )
        conn.commit()
        conn.close()
