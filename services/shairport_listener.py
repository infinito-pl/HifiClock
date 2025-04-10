def read_shairport_metadata():
    global last_title, last_artist, last_album, last_cover, active_state

    try:
        proc = subprocess.Popen(
            ["/usr/local/bin/shairport-sync-metadata-reader"],
            stdin=open("/tmp/shairport-sync-metadata", "rb"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

        title = artist = album = cover_path = None
        start_time = time.time()

        while True:
            line = proc.stdout.readline()
            if not line:
                continue

            line = line.strip()

            if "[DEBUG] Enter Active State" in line:
                active_state = True
                print("[DEBUG] Entered Active State. Start reading metadata.")
                continue
            elif "[DEBUG] Exit Active State" in line:
                active_state = False
                print("[DEBUG] Exit Active State. Stopping metadata reading.")
                return last_title, last_artist, last_album, last_cover, False

            if active_state:
                if line.startswith("Title:"):
                    title = clean_value(line.split(': "', 1)[1].strip('".'))
                elif line.startswith("Artist:"):
                    artist = clean_value(line.split(': "', 1)[1].strip('".'))
                elif line.startswith("Album Name:"):
                    album = clean_value(line.split(': "', 1)[1].strip('".'))
                elif "Picture received" in line and "length" in line:
                    cover_path = "/tmp/shairport-sync/.cache/coverart/last_cover.jpg"

                # Jeśli metadane się zmieniły, zaktualizuj
                if title != last_title or artist != last_artist or album != last_album or cover_path != last_cover:
                    last_title = title
                    last_artist = artist
                    last_album = album
                    last_cover = cover_path
                    return title, artist, album, cover_path, True

            # Sprawdzanie co 0.1 sekundy, zamiast czekać przez 1 sekundę
            if time.time() - start_time > 0.1:
                start_time = time.time()  # Resetujemy czas, aby sprawdzać częściej

        return last_title, last_artist, last_album, last_cover, False

    except Exception as e:
        print(f"[DEBUG] Failed to run reader: {e}")
        return last_title, last_artist, last_album, last_cover, False