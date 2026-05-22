import json
import os
import mysql.connector

CONFIG_PATH = "/etc/hearts-of-space/mysql.json"
DATA_DIR = "/home/rtoews/projects/hearts-of-space-data/json"

with open(CONFIG_PATH, "r") as f:
    db_config = json.load(f)

conn = mysql.connector.connect(
    host=db_config["host"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"],
)

cursor = conn.cursor()

loaded_count = 0
skipped_count = 0

for filename in sorted(
    os.listdir(DATA_DIR),
    key=lambda x: int(x.replace(".json", ""))
):
    if not filename.endswith(".json"):
        continue

    path = os.path.join(DATA_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    program_id = data.get("id")
    program_number = data.get("number")
    program_title = data.get("title")

    if program_id is None:
        print(f"Skipping {filename}; no program id")
        continue

    cursor.execute(
        "SELECT 1 FROM programs WHERE id = %s LIMIT 1",
        (program_id,),
    )

    if cursor.fetchone():
        print(f"Skipping program {program_id} / {program_number}: already loaded")
        skipped_count += 1
        continue

    print(f"Loading program {program_id} / {program_number}: {program_title}")

    short_desc = data.get("shortDescription")
    description = data.get("description")
    weather = data.get("weatherReport")
    program_date = data.get("date")
    producer = data.get("producer")
    popularity = data.get("popularity")
    gallery_url = data.get("galleryUrl")
    genres = data.get("genres") or []
    albums = data.get("albums") or []
    raw_json = json.dumps(data)

    # 1. Insert parent program first.
    cursor.execute("""
        INSERT INTO programs
          (id, program_number, title, short_description, description, weather_report,
           program_date, producer, popularity, gallery_url, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        program_id,
        program_number,
        program_title,
        short_desc,
        description,
        weather,
        program_date,
        producer,
        popularity,
        gallery_url,
        raw_json,
    ))

    for album in albums:
        album_id = album.get("id")

        if album_id is None:
            continue

        # 2. Insert album.
        cursor.execute("""
            INSERT INTO albums
              (id, title, album_date, label_name, buy_cd_url, playable, album_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              title = VALUES(title),
              album_date = VALUES(album_date),
              label_name = VALUES(label_name),
              buy_cd_url = VALUES(buy_cd_url),
              playable = VALUES(playable),
              album_type = VALUES(album_type)
        """, (
            album_id,
            album.get("title"),
            album.get("date"),
            (album.get("label") or {}).get("name"),
            album.get("buyCdUrl"),
            album.get("playable"),
            album.get("albumType"),
        ))

        # 3. Insert album artists and album_artists links.
        for artist in album.get("artists") or []:
            artist_id = artist.get("id")

            if artist_id is None:
                continue

            cursor.execute("""
                INSERT INTO artists
                  (id, name, sort_name, url, email)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  name = VALUES(name),
                  sort_name = VALUES(sort_name),
                  url = VALUES(url),
                  email = VALUES(email)
            """, (
                artist_id,
                artist.get("name"),
                artist.get("sortName"),
                artist.get("url"),
                artist.get("email"),
            ))

            cursor.execute("""
                INSERT IGNORE INTO album_artists
                  (album_id, artist_id)
                VALUES (%s, %s)
            """, (
                album_id,
                artist_id,
            ))

        # 4. Insert tracks, track artists, track_artists, and program_tracks.
        for track in album.get("tracks") or []:
            track_id = track.get("id")
            track_title = track.get("title")

            if track_id is None or not track_title:
                continue

            cursor.execute("""
                INSERT INTO tracks
                  (id, title)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                  title = VALUES(title)
            """, (
                track_id,
                track_title,
            ))

            for artist in track.get("artists") or []:
                artist_id = artist.get("id")

                if artist_id is None:
                    continue

                cursor.execute("""
                    INSERT INTO artists
                      (id, name, sort_name, url, email)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                      name = VALUES(name),
                      sort_name = VALUES(sort_name),
                      url = VALUES(url),
                      email = VALUES(email)
                """, (
                    artist_id,
                    artist.get("name"),
                    artist.get("sortName"),
                    artist.get("url"),
                    artist.get("email"),
                ))

                cursor.execute("""
                    INSERT IGNORE INTO track_artists
                      (track_id, artist_id)
                    VALUES (%s, %s)
                """, (
                    track_id,
                    artist_id,
                ))

            cursor.execute("""
                INSERT INTO program_tracks
                  (program_id, track_id, album_id,
                   start_position_in_stream, duration, attributes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  album_id = VALUES(album_id),
                  start_position_in_stream = VALUES(start_position_in_stream),
                  duration = VALUES(duration),
                  attributes = VALUES(attributes)
            """, (
                program_id,
                track_id,
                album_id,
                track.get("startPositionInStream"),
                track.get("duration"),
                track.get("attributes"),
            ))

    # 5. Insert genres and program_genres links.
    for genre in genres:
        genre_id = genre.get("id")
        genre_name = genre.get("name")

        if genre_id is None or not genre_name:
            continue

        cursor.execute("""
            INSERT INTO genres
              (id, name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
              name = VALUES(name)
        """, (
            genre_id,
            genre_name,
        ))

        cursor.execute("""
            INSERT INTO program_genres
              (program_id, genre_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
              genre_id = genre_id
        """, (
            program_id,
            genre_id,
        ))

    conn.commit()
    loaded_count += 1

cursor.close()
conn.close()

print(f"Done. Loaded {loaded_count} new programs. Skipped {skipped_count} existing programs.")
