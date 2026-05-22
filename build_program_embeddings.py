import json
import time
import os
import mysql.connector
from openai import OpenAI

CONFIG_PATH = "/etc/hearts-of-space/mysql.json"
MODEL = "text-embedding-3-small"

# OpenAI key
with open(os.path.expanduser("/etc/hearts-of-space/.openai_key"), "r", encoding="utf-8") as f:
    os.environ["OPENAI_API_KEY"] = f.read().strip()

client = OpenAI()

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    db_config = json.load(f)

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT
      id,
      program_number,
      title,
      short_description,
      description,
      weather_report
    FROM programs
    WHERE id NOT IN (
      SELECT program_id FROM program_embeddings
    )
    ORDER BY program_number
""")

rows = cursor.fetchall()

print(f"Found {len(rows)} programs needing embeddings.")

insert_sql = """
    INSERT INTO program_embeddings
      (program_id, source_text, embedding)
    VALUES
      (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
      source_text = VALUES(source_text),
      embedding = VALUES(embedding),
      created_at = CURRENT_TIMESTAMP
"""

for row in rows:
    parts = [
        f"Program {row['program_number']}: {row['title']}",
        row.get("short_description") or "",
        row.get("description") or "",
        row.get("weather_report") or "",
    ]

    source_text = "\n\n".join(part for part in parts if part.strip())

    try:
        result = client.embeddings.create(
            model=MODEL,
            input=source_text
        )

        embedding = result.data[0].embedding
        embedding_json = json.dumps(embedding)

        cursor.execute(insert_sql, (
            row["id"],
            source_text,
            embedding_json
        ))

        conn.commit()

        print(f"Embedded {row['program_number']}: {row['title']}")

        time.sleep(0.1)

    except Exception as e:
        print(f"ERROR on {row['program_number']} {row['title']}: {e}")
        conn.rollback()
        time.sleep(2)

cursor.close()
conn.close()

print("Done.")
