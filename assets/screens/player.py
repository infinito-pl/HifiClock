import os
import pygame
import cairosvg
import io
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def truncate_text(text, max_length=30):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."

def load_and_render_svg(file_path, width, height):
    svg_data = cairosvg.svg2png(url=file_path)
    icon_image = pygame.image.load(io.BytesIO(svg_data))
    icon_image = pygame.transform.scale(icon_image, (width, height))
    return icon_image

def run_player_screen(screen, metadata, test_mode=False):
    WIDTH, HEIGHT = 800, 800
    CENTER_X = WIDTH // 2
    CENTER_Y = HEIGHT // 2
    SWIPE_THRESHOLD = 0.25
    start_y = None

    clock = pygame.time.Clock()

    WHITE = (255, 255, 255)
    BACKGROUND_COLOR = (30, 30, 30)

    font_regular_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Regular.ttf")
    font_bold_path = os.path.join(BASE_DIR, "assets", "fonts", "Barlow-Bold.ttf")

    font_artist = pygame.font.Font(font_bold_path, 50)
    font_album = pygame.font.Font(font_regular_path, 30)
    font_title = pygame.font.Font(font_regular_path, 50)

    play_icon = load_and_render_svg(os.path.join(BASE_DIR, "assets", "icons", "btn_play.svg"), 158, 158)
    pause_icon = load_and_render_svg(os.path.join(BASE_DIR, "assets", "icons", "btn_pause.svg"), 158, 158)

    default_cover = os.path.join(BASE_DIR, "assets", "images", "cover.png")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.FINGERDOWN:
                start_y = event.y * HEIGHT
            elif event.type == pygame.FINGERUP and start_y is not None:
                end_y = event.y * HEIGHT
                delta_y = start_y - end_y
                if delta_y > SWIPE_THRESHOLD:
                    pygame.event.clear()
                    return "clock"
                start_y = None

        screen.fill(BACKGROUND_COLOR)

        # Use metadata from main.py
        title = metadata.get("title", " ")
        artist = metadata.get("artist", " ")
        album = metadata.get("album", " ")
        cover_path = metadata.get("cover_path", default_cover)
        is_playing = metadata.get("active_state", False)

        if not os.path.isfile(cover_path):
            cover_path = default_cover

        # Draw cover art
        try:
            cover = pygame.image.load(cover_path)
            cover = pygame.transform.scale(cover, (WIDTH, HEIGHT))
            cover.set_alpha(int(0.4 * 255))
            screen.blit(cover, (0, 0))
        except Exception as e:
            logger.error(f"Error loading cover art: {e}")
            cover = pygame.image.load(default_cover)
            cover = pygame.transform.scale(cover, (WIDTH, HEIGHT))
            cover.set_alpha(int(0.4 * 255))
            screen.blit(cover, (0, 0))

        # Draw overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # Render text
        artist = truncate_text(artist)
        album = truncate_text(album)
        title = truncate_text(title)

        if artist:
            artist_surface = font_artist.render(artist, True, WHITE)
            screen.blit(artist_surface, (CENTER_X - artist_surface.get_width() // 2, CENTER_Y - 175))
        if album:
            album_surface = font_album.render(album, True, WHITE)
            screen.blit(album_surface, (CENTER_X - album_surface.get_width() // 2, CENTER_Y - 100))
        if title:
            title_surface = font_title.render(title, True, WHITE)
            screen.blit(title_surface, (CENTER_X - title_surface.get_width() // 2, CENTER_Y + 100))

        # Render play/pause icon
        icon = pause_icon if is_playing else play_icon
        screen.blit(icon, (CENTER_X - icon.get_width() // 2, CENTER_Y - icon.get_height() // 2))

        pygame.display.flip()
        clock.tick(30)
