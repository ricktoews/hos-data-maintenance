import json
import sys
import os
import math
import mysql.connector
from openai import OpenAI

CONFIG_PATH = "/etc/hearts-of-space/mysql.json"
MODEL = "text-embedding-3-small"
DEFAULT_LIMIT = 10

# OpenAI key
with open(os.path.expanduser("/etc/hearts-of-space/.openai_key"), "r", encoding="utf-8") as f:
    os.environ["OPENAI_API_KEY"] = f.read().strip()

client = OpenAI()


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0

    return dot / (norm_a * norm_b)


def main():
    if len(sys.argv) < 2:
        print('Usage: python search_programs_by_mood.py "rainy day, quiet, reflective" [limit]')
        sys.exit(1)

    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_LIMIT

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        db_config = json.load(f)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    print(f'Embedding query: "{query}"')

    query_embedding = client.embeddings.create(
        model=MODEL,
        input=query
    ).data[0].embedding

    cursor.execute("""
        SELECT
          p.program_number,
          p.title,
          p.short_description,
          p.weather_report,
          pe.embedding
        FROM program_embeddings pe
        JOIN programs p ON p.id = pe.program_id
    """)

    results = []

    for row in cursor:
        program_embedding = json.loads(row["embedding"])
        score = cosine_similarity(query_embedding, program_embedding)

        results.append({
            "score": score,
            "program_number": row["program_number"],
            "title": row["title"],
            "short_description": row["short_description"],
            "weather_report": row["weather_report"],
        })

    cursor.close()
    conn.close()

    results.sort(key=lambda r: r["score"], reverse=True)

    print()
    print(f"Top {limit} matches:")
    print("-" * 80)

    for i, result in enumerate(results[:limit], start=1):
        print(f"{i}. #{result['program_number']} — {result['title']}")
        print(f"   Score: {result['score']:.4f}")

        if result["short_description"]:
            print(f"   {result['short_description']}")

        if result["weather_report"]:
            print(f"   Weather report: {result['weather_report']}")

        print()


if __name__ == "__main__":
    main()
