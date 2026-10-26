"""Export the current Dark Folklore artwork without rebuilding the source books."""
from pathlib import Path
import hashlib
import json
import re
import shutil

from PIL import Image, ImageOps
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh(source, books):
    designs = {b['number']: b for b in json.loads((source / 'cover-concepts/dark-folklore-designs.json').read_text(encoding='utf-8'))}
    covers = ROOT / 'assets/covers'
    scenes = ROOT / 'assets/scenes'
    covers.mkdir(exist_ok=True)
    scenes.mkdir(exist_ok=True)
    records = []
    for b in books:
        directory = source / f'book{b["number"]:02}'
        master = directory / 'images-print/background-dark-folklore-master.png'
        if not master.is_file():
            raise FileNotFoundError(master)
        art = directory / 'images-print/cover-print-ready-no-barcode.png'
        metadata = directory / 'build-metadata.json'
        design = designs[b['number']]
        b['accent'] = '#' + ''.join(f'{v:02x}' for v in design['accent'])
        if art.is_file() and metadata.is_file():
            geometry = json.loads(metadata.read_text(encoding='utf-8'))['print']
            wrap = Image.open(art).convert('RGB')
            assert wrap.size == (geometry['cover_width_px'], geometry['cover_height_px']), art
            dpi = geometry['dpi']
            left = wrap.width - round((geometry['trim_width_in'] + geometry['bleed_in']) * dpi)
            top = round(geometry['bleed_in'] * dpi)
            crop = [left, top, left + round(geometry['trim_width_in'] * dpi), top + round(geometry['trim_height_in'] * dpi)]
            front = wrap.crop(crop)
            size = [900, round(front.height * 900 / front.width)]
            b['cover'] = f'/assets/covers/{b["slug"]}.webp'
            front.resize(tuple(size), Image.Resampling.LANCZOS).save(ROOT / b['cover'].lstrip('/'), quality=89, method=6)
            front.save(covers / f'{b["slug"]}.jpg', quality=93, optimize=True)
            b.update(size=size, source_art=art.relative_to(source).as_posix(), source_crop=crop, source_art_sha256=fingerprint(art))
            cover_kind = 'finished print cover'
        else:
            # New illustrations can be shown before print geometry exists, but
            # must not be presented as completed covers or publication evidence.
            b['cover'] = None
            b['size'] = [900, 1389]
            b['source_art'] = master.relative_to(source).as_posix()
            b.pop('source_crop', None)
            b['source_art_sha256'] = fingerprint(master)
            cover_kind = 'illustration preview; finished cover forthcoming'
        scene = Image.open(master).convert('RGB')
        b['artwork'] = f'/assets/scenes/{b["slug"]}.webp'
        b['artwork_thumb'] = f'/assets/scenes/{b["slug"]}-thumb.webp'
        b['source_scene'] = master.relative_to(source).as_posix()
        ImageOps.fit(scene, (1600, 900), Image.Resampling.LANCZOS, centering=(.65, .58)).save(ROOT / b['artwork'].lstrip('/'), quality=87, method=6)
        ImageOps.fit(scene, (480, 300), Image.Resampling.LANCZOS, centering=(.68, .58)).save(ROOT / b['artwork_thumb'].lstrip('/'), quality=86, method=6)
        if b['number'] == 1:
            hero = ImageOps.fit(scene, (1920, 1080), Image.Resampling.LANCZOS, centering=(.65, .58))
            hero.save(ROOT / 'assets/hero-crossroads.webp', quality=90, method=6)
            hero.save(ROOT / 'assets/hero-crossroads.png', optimize=True)
            hero.save(ROOT / 'assets/seer-collections/seer-fairies-20261022.webp', quality=90, method=6)
        copy_path = directory / 'images-print/cover-copy.txt'
        parts = re.split(r'(?m)^## ([A-Z][A-Z ]*)[ \t]*$', copy_path.read_text(encoding='utf-8-sig'))
        jacket = {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}
        required = ('FRONT TAGLINE', 'BOOK TYPE', 'BACK HOOK', 'BACK KICKER', 'BACK BLURB', 'BACK CLOSING')
        assert all(jacket.get(key) for key in required), copy_path
        b['copy'] = {key: jacket[key] for key in required}
        b['source_copy'] = copy_path.relative_to(source).as_posix()
        b['copy_kind'] = 'approved cover text'
        records.append({'number': b['number'], 'title': b['title'], 'cover_kind': cover_kind, 'source_art': b['source_art'], 'source_art_sha256': b['source_art_sha256'], 'source_scene': b['source_scene'], 'source_scene_sha256': fingerprint(master), 'cover': b['cover'], 'artwork': b['artwork'], 'accent': b['accent']})
        print(f'Synced case {b["number"]:02}: {b["title"]} ({cover_kind})', flush=True)
    fonts = ROOT / 'assets/fonts'
    for name in ('AlegreyaSC-Black', 'Charter-Regular', 'Charter-Italic', 'Charter-Bold'):
        font = TTFont(source / 'fonts' / f'{name}.ttf')
        options = subset.Options()
        options.flavor = 'woff'
        worker = subset.Subsetter(options=options)
        worker.populate(unicodes=list(range(0x250)) + list(range(0x2010, 0x2028)) + list(range(0x2190, 0x219A)))
        worker.subset(font)
        font.flavor = 'woff'
        font.save(fonts / f'{name}.woff')
    for name in ('AlegreyaSC-OFL.txt', 'Charter-LICENSE.txt'):
        shutil.copyfile(source / 'fonts' / name, fonts / name)
    for name in ('author', 'logo'):
        image = Image.open(source / 'assets' / f'{name}.png').convert('RGB')
        image.thumbnail((900, 900), Image.Resampling.LANCZOS)
        image.save(ROOT / 'assets' / f'{name}.webp', quality=90, method=6)
    (ROOT / 'data/fairies-artwork.json').write_text(json.dumps({'source': 'SEERFAIRIES', 'books': records}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    registry = ROOT / 'data/seer-collections.json'
    if registry.is_file():
        data = json.loads(registry.read_text(encoding='utf-8'))
        current = next(b for b in data['collections'] if b['slug'] == 'seer-fairies')
        current.update(width=1920, height=1080, alt='An engraved black horse watches an autumn crossroads beneath a gold evening sky, from The Púca cover artwork')
        registry.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return books
