# metadata_shairport.py

import os
import select
import struct
import time

PIPE_PATH = "/tmp/shairport-sync-metadata"
TMP_COVER = "/tmp/cover.jpg"  # lub .png – w trakcie parsowania sprawdzisz magic number

def get_current_track_info_shairport():
    """
    Nieblokujące odczytywanie metadanych z potoku Shairport Sync w formacie chunków.
    Zwraca (title, artist, album, cover_path).
    Jeżeli brak danych w potoku – zwraca (None, None, None, None) natychmiast (bez blokowania).
    """

    if not os.path.exists(PIPE_PATH):
        # Potok nie istnieje
        return (None, None, None, None)

    # Otwieramy potok w trybie non-blocking
    try:
        fd = os.open(PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as e:
        # Nie udało się otworzyć
        return (None, None, None, None)

    # Sprawdzamy selectem, czy coś jest do odczytu (bez czekania)
    rlist, _, _ = select.select([fd], [], [], 0)
    if fd not in rlist:
        # Brak danych
        os.close(fd)
        return (None, None, None, None)

    # Staramy się przeczytać pewną ilość bajtów – na przykład 65536
    # (uwzględniając że okładka może być spora)
    try:
        raw_data = os.read(fd, 65536)
    except OSError:
        os.close(fd)
        return (None, None, None, None)

    os.close(fd)
    if not raw_data:
        return (None, None, None, None)

    # Parsujemy chunki:
    # Każdy chunk ma postać:
    #   4 bajty: "ssnc"
    #   4 bajty: kod (np. minm, asar, etc.)
    #   8 bajtów: big-endian integer = length
    #   length bajtów danych

    # Będziemy iterować po raw_data, wyłuskiwać chunki i sprawdzać kody
    idx = 0
    data_len = len(raw_data)

    title = None
    artist = None
    album = None
    cover_path = None

    while idx < data_len:
        if (idx + 16) > data_len:
            # za mało danych na kolejny chunk
            break

        # Sprawdzamy nagłówek "ssnc"
        signature = raw_data[idx:idx+4]
        if signature != b'ssnc':
            # jeżeli chunk nie pasuje, np. metadata start/end – pomijamy
            # np. "ssnc" wcale nie jest – przesuńmy się kawałek do przodu
            idx += 1
            continue

        code = raw_data[idx+4:idx+8]   # np. b'minm'
        length_bytes = raw_data[idx+8:idx+16]  # 8 bajtów big-endian
        length = struct.unpack(">Q", length_bytes)[0]  # big-endian 64-bit

        # Przesuwamy się do payload
        idx += 16
        if idx + length > data_len:
            # Brak wystarczającej ilości danych
            break

        payload = raw_data[idx: idx + length]
        idx += length  # pchamy wskaźnik

        # Parsujemy wg kodu
        if code == b'minm':
            # Tytuł utworu
            # w payload mamy ASCII/UTF-8
            title = payload.decode("utf-8", errors="replace")
        elif code == b'asar':
            artist = payload.decode("utf-8", errors="replace")
        elif code == b'asal':
            album = payload.decode("utf-8", errors="replace")
        elif code in (b'PICT', b'pic ', b'covr'):
            # Okładka
            # Zapiszmy do pliku tymczasowego:
            try:
                with open(TMP_COVER, "wb") as f:
                    f.write(payload)
                cover_path = TMP_COVER
            except:
                pass
        else:
            # inne kody ignorujemy
            pass

    return (title, artist, album, cover_path)