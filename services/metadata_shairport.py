# metadata_shairport.py

import os
import select

PIPE_PATH = "/tmp/shairport-sync-metadata"  # przykładowa ścieżka potoku

def get_current_track_info_shairport():
    """
    Nieblokujący odczyt z potoku Shairport Sync, zwraca (title, artist, album, cover_path).
    Jeśli brak danych, zwraca None, None, None, None.
    """

    if not os.path.exists(PIPE_PATH):
        # Potok nie istnieje -> brak danych
        return None, None, None, None

    # Otwieramy w trybie non-blocking
    try:
        fd = os.open(PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as e:
        # Nie da się otworzyć – np. błąd dostępu
        print("[shairport] Błąd otwierania potoku:", e)
        return None, None, None, None

    # Za pomocą select sprawdzamy, czy coś jest do odczytania
    # Timeout=0 – nie blokujemy się w ogóle, jeżeli nic nie ma
    rlist, _, _ = select.select([fd], [], [], 0)
    if fd not in rlist:
        # Brak danych -> oddaj None
        os.close(fd)
        return None, None, None, None

    # Odczytujemy np. 4096 bajtów
    try:
        raw_data = os.read(fd, 4096)
    except OSError as e:
        print("[shairport] Błąd read() z potoku:", e)
        os.close(fd)
        return None, None, None, None

    os.close(fd)
    if not raw_data:
        # Pusty odczyt = brak danych
        return None, None, None, None

    # Tutaj musisz zaimplementować parsowanie surowych danych z potoku
    # – w oryginale Shairport Sync wysyła tzw. „kodeki” (metadane w formie chunków).
    # Dla przykładu:
    text = raw_data.decode("utf-8", errors="replace")

    # Sztuczny parser do demonstracji:
    #   Title=..., Artist=..., Album=..., CoverPath=...
    # Oczywiście w praktyce format metadanych jest bardziej złożony.

    # Przykład "Title=Song Title\nArtist=XYZ\nAlbum=Hello\nCoverPath=/tmp/...":
    title, artist, album, cover_path = None, None, None, None

    lines = text.splitlines()
    for line in lines:
        if line.startswith("Title="):
            title = line[6:].strip()
        elif line.startswith("Artist="):
            artist = line[7:].strip()
        elif line.startswith("Album="):
            album = line[6:].strip()
        elif line.startswith("CoverPath="):
            cover_path = line[10:].strip()

    return (title, artist, album, cover_path)