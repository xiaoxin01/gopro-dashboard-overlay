import asyncio
import io
import itertools
from typing import List

import PIL
from PIL.Image import Image
from geotiler.map import _find_top_left_tile, _tile_coords, _tile_offsets, Tile

from gopro_overlay.log import log


# Attempt at re-implementing the rendering part of geotiler with a view on performance
# Use downloader as per geotiler

class ImageTileCache:

    retry_delays = (1, 2, 4)

    def __init__(self):
        self.cache = {}

    async def do_async_download(self, downloader, tiles: List[Tile]):
        gen = downloader(tiles, 1)
        l = []
        async for g in gen:
            l.append(g)
        return l

    def do_download(self, downloader, tiles: List[Tile]) -> List[Tile]:
        task = self.do_async_download(downloader, tiles)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(task)

    def do_download_with_retries(self, downloader, tiles: List[Tile]) -> List[Tile]:
        if not tiles:
            return []

        downloaded = self.do_download(downloader, tiles)
        downloaded_by_url = {d.url: d for d in downloaded}

        for retry, delay in enumerate(self.retry_delays, start=1):
            missing = [t for t in tiles if downloaded_by_url.get(t.url, t).img is None]
            if not missing:
                break

            log(f"Retrying {len(missing)} map tile download(s), attempt {retry}/{len(self.retry_delays)}")
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(delay))

            for d in self.do_download(downloader, missing):
                downloaded_by_url[d.url] = d

        return [downloaded_by_url.get(t.url, t) for t in tiles]

    def as_image(self, data):
        f = io.BytesIO(data)
        return PIL.Image.open(f).convert('RGBA')

    def populate(self, downloader, tiles: List[Tile]):

        # Populate image directly for those we know already
        def c(t):
            if t.url in self.cache:
                return t._replace(img=self.cache[t.url])
            return t

        tiles = [c(t) for t in tiles]

        have = [t for t in tiles if t.img is not None]
        have_not = [t for t in tiles if t.img is None]

        # Now use existing download to download
        downloaded = self.do_download_with_retries(downloader, have_not)

        converted = []

        for d in downloaded:
            if d.img is None:
                log(f"Unable to download map tile after retries: {d.url}")
                converted.append(d)
                continue
            else:
                try:
                    img = self.as_image(d.img)
                except OSError as e:
                    # somehow the image data is invalid...
                    log(f"Unable to load image data from {d.url} - {e}")
                    converted.append(d._replace(img=None))
                    continue

            self.cache[d.url] = img
            converted.append(d._replace(img=img))

        return list(itertools.chain(have, converted))


cache = ImageTileCache()


def my_render_map(map, tiles, downloader, **kwargs):
    tile_url = map.provider.tile_url

    coord, offset = _find_top_left_tile(map)
    coords = _tile_coords(map, coord, offset)
    offsets = _tile_offsets(map, offset)
    urls = (tile_url(c, map.zoom) for c in coords)
    tiles = list((Tile(u, o, None, None) for u, o in zip(urls, offsets)))

    tiles = cache.populate(downloader, tiles)

    image = PIL.Image.new('RGBA', tuple(map.size))

    for tile in tiles:
        if tile.img is not None:
            image.paste(tile.img, tile.offset)

    return image
