# services/metadata_shairport.py

import os
import time

PIPE_PATH = "/tmp/shairport-sync-metadata"

def get_current_track_info_shairport():
    """
    Zwraca krotkę (title, artist, album, cover_image_path).
    Lub (None, None, None, None), jeśli jeszcze nic nie wiadomo.

    Uwaga: W tym przykładzie odczytujemy tylko ostatnie metadane 
    ze strumienia i zakładamy, że od momentu startu Shairport 
    (bądź odtwarzania) w pipe przychodzą kolejne ramki 'ssnc' 
    z różnymi kodami, np. 'asar' (artist), 'asal' (album), 'minm' (title).
    """

    # Zmiennie globalne / modułowe, w których przechowujemy bieżące metadane
    global last_title, last_artist, last_album, last_cover_path

    # Jeśli wcześniej nie zainicjalizowaliśmy
    if "last_title" not in globals():
        last_title = None
        last_artist = None
        last_album = None
        last_cover_path = None

    # Sprawdzamy, czy potok w ogóle istnieje
    if not os.path.exists(PIPE_PATH):
        # Shairport Sync jeszcze nie utworzył metadanych
        return (last_title, last_artist, last_album, last_cover_path)

    # Otwieramy potok w trybie 'rb' (binarne), bo niektóre metadane (okładka) są binarne
    # Ale tu w ramach uproszczenia wczytujemy TYLKO to co jest obecnie w buforze.
    try:
        with open(PIPE_PATH, "rb") as f:
            # Odczytujemy *całą* zawartość
            data = f.read()

        # Przetwarzamy (w prosty sposób) to, co przyszło
        # Shairport Sync wysyła w formacie, gdzie występują:
        #  8-bajtowe nagłówki (4 bajty type tagu, 4 bajty długość)
        #  plus payload
        #  Możesz w sieci znaleźć specyfikację "shairport-sync metadata".
        idx = 0
        while idx < len(data):
            if idx + 8 > len(data):
                break
            # Odczytujemy 8 bajtów
            tag_type = data[idx:idx+4]   # np. b'ssnc'
            length_bytes = data[idx+4:idx+8]
            length = int.from_bytes(length_bytes, byteorder='big')
            idx += 8

            # Odczytujemy payload
            payload = data[idx: idx+length]
            idx += length

            # Parsujemy, jeśli type to 'ssnc' + 4 bajty kodu (w payload)
            # W rzeczywistości jest to bardziej skomplikowane, ale tu uproszczony schemat
            if tag_type == b'ssnc':
                if length < 8:
                    continue
                code = payload[0:4]  # np. b'asar' (artist)
                content = payload[4:]
                
                # Artist
                if code == b'asar':
                    last_artist = content.decode('utf-8', errors='ignore')
                # Album
                elif code == b'asal':
                    last_album = content.decode('utf-8', errors='ignore')
                # Title
                elif code == b'minm':
                    last_title = content.decode('utf-8', errors='ignore')
                # Okładka (tu TYLKO do pliku)
                elif code == b'PICT':
                    # 'PICT' to cover art, często w formacie JPEG/PNG w payload
                    # Zapiszmy do pliku tymczasowego
                    cover_path = "/tmp/shairport-cover.jpg"
                    try:
                        with open(cover_path, "wb") as cf:
                            cf.write(content)
                        last_cover_path = cover_path
                    except:
                        pass
                else:
                    # Inne typy metadanych pomijamy
                    pass

    except Exception as e:
        # Nie udało się otworzyć / parsować
        # Zwracamy stan obecny
        return (last_title, last_artist, last_album, last_cover_path)

    return (last_title, last_artist, last_album, last_cover_path)