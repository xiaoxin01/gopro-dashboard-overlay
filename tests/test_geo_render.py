import io

import PIL.Image
from geotiler.map import Tile

from gopro_overlay.geo_render import ImageTileCache


def png_bytes(colour):
    output = io.BytesIO()
    PIL.Image.new("RGBA", (1, 1), colour).save(output, format="PNG")
    return output.getvalue()


def test_populate_retries_failed_tile_downloads():
    cache = ImageTileCache()
    cache.retry_delays = (0, 0, 0)
    attempts = 0
    image_bytes = png_bytes((255, 0, 0, 255))
    tile = Tile("tile-url", (0, 0), None, None)

    async def downloader(tiles, limit):
        nonlocal attempts
        attempts += 1
        for t in tiles:
            if attempts < 4:
                yield t
            else:
                yield t._replace(img=image_bytes)

    populated = cache.populate(downloader, [tile])

    assert attempts == 4
    assert populated[0].img.getpixel((0, 0)) == (255, 0, 0, 255)


def test_populate_leaves_failed_tile_empty_after_retries():
    cache = ImageTileCache()
    cache.retry_delays = (0, 0, 0)
    attempts = 0
    tile = Tile("tile-url", (0, 0), None, None)

    async def downloader(tiles, limit):
        nonlocal attempts
        attempts += 1
        for t in tiles:
            yield t

    populated = cache.populate(downloader, [tile])

    assert attempts == 4
    assert populated[0].img is None
    assert tile.url not in cache.cache
