import json
import os
import mysql.connector

CONFIG_PATH = "/etc/hearts-of-space/mysql.json"
DATA_DIR = "/home/rtoews/projects/hearts-of-space-data/json"

# Load DB config
with open(CONFIG_PATH, "r") as f:
    db_config = json.load(f)

conn = mysql.connector.connect(
    host=db_config["host"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"]
)

cursor = conn.cursor()

for filename in os.listdir(DATA_DIR):
    if not filename.endswith(".json"):
        continue

    path = os.path.join(DATA_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    id = data.get("id")
    title = data.get("title")
    short_desc = data.get("shortDescription")
    description = data.get("description")
    weather = data.get("weatherReport")
    date = data.get("date")
    producer = data.get("producer")
    popularity = data.get("popularity")
    gallery_url = data.get("galleryUrl")
    genres = data.get("genres") or []


    for album in data.get("albums") or []:
        album_id = album.get("id")

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
            album.get("albumType")
        ))

        for artist in album.get("artists") or []:
            artist_id = artist.get("id")
            if artist_id is None:
                continue

            cursor.execute("""
                INSERT INTO artists (id, name, sort_name, url, email)
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
                artist.get("email")
            ))

            cursor.execute("""
                INSERT IGNORE INTO album_artists (album_id, artist_id)
                VALUES (%s, %s)
            """, (album_id, artist_id))

        for track in album.get("tracks") or []:
            track_id = track.get("id")

            # existing tracks/program_tracks inserts here

            for artist in track.get("artists") or []:
                artist_id = artist.get("id")
                if artist_id is None:
                    continue

                cursor.execute("""
                    INSERT INTO artists (id, name, sort_name, url, email)
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
                    artist.get("email")
                ))

                cursor.execute("""
                    INSERT IGNORE INTO track_artists (track_id, artist_id)
                    VALUES (%s, %s)
                """, (track_id, artist_id))




    for album in data.get("albums") or []:
        album_id = album.get("id")

        for track in album.get("tracks") or []:
            track_id = track.get("id")
            title = track.get("title")

            if track_id is None or not title:
                continue

            cursor.execute("""
                INSERT INTO tracks (id, title)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                  title = VALUES(title)
            """, (track_id, title))

            cursor.execute("""
                INSERT INTO program_tracks
                  (program_id, track_id, album_id, start_position_in_stream, duration, attributes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  album_id = VALUES(album_id),
                  start_position_in_stream = VALUES(start_position_in_stream),
                  duration = VALUES(duration),
                  attributes = VALUES(attributes)
            """, (
                id,
                track_id,
                album_id,
                track.get("startPositionInStream"),
                track.get("duration"),
                track.get("attributes")
            ))




    for genre in genres:
        genre_id = genre.get("id")
        genre_name = genre.get("name")

        if genre_id is None or not genre_name:
            continue

        cursor.execute("""
            INSERT INTO genres (id, name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name)
        """, (genre_id, genre_name))

        cursor.execute("""
            INSERT INTO program_genres (program_id, genre_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE genre_id = genre_id
        """, (id, genre_id))


    raw_json = json.dumps(data)

    sql = """
        INSERT INTO programs
        (id, title, short_description, description, weather_report,
         program_date, producer, popularity, gallery_url, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title)
    """

    cursor.execute(sql, (
        id, title, short_desc, description, weather,
        date, producer, popularity, gallery_url, raw_json
    ))

conn.commit()
cursor.close()
conn.close()
