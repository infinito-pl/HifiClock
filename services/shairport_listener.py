def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover

    try:
        proc = subprocess.Popen(
            ["shairport-sync-metadata-reader", "--raw", "/tmp/shairport-sync-metadata"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )

        title = None
        artist = None
        album = None
        cover_path = None

        start_time = time.time()

        while True:
            line = proc.stdout.readline()
            if not line:
                continue

            line = line.strip()

            if line.startswith("Title:"):
                title = clean_value(line.replace("Title:", ""))
            elif line.startswith("Artist:"):
                artist = clean_value(line.replace("Artist:", ""))
            elif line.startswith("Album Name:"):
                album = clean_value(line.replace("Album Name:", ""))
            elif "Picture received, length" in line:
                try:
                    files = sorted(os.listdir(COVER_ART_PATH), key=lambda x: os.path.getmtime(os.path.join(COVER_ART_PATH, x)), reverse=True)
                    if files:
                        cover_path = os.path.join(COVER_ART_PATH, files[0])
                except:
                    pass

            # Sprawdzamy, czy metadane się zmieniły
            if title and artist and album:
                updated = (title != last_title or artist != last_artist or album != last_album or cover_path != last_cover)
                if updated:  # Zaktualizuj tylko wtedy, gdy są nowe dane
                    last_title = title
                    last_artist = artist
                    last_album = album
                    last_cover = cover_path
                    return title, artist, album, cover_path, updated

            if time.time() - start_time > 10:
                break

        return last_title, last_artist, last_album, last_cover, False

    except Exception as e:
        print("[shairport_listener] Błąd:", e)
        return last_title, last_artist, last_album, last_cover, False
