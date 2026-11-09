#!/usr/bin/env python3
"""Build private D16 HD texture packs from owned-disc captures; do not publish packs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile
import texture_sample

SLUG = re.compile(r'[A-Za-z0-9_-]{1,48}\Z')
MAX_ENTRIES = 8

def compile_pack(spec_path, output_dir):
    spec_path = Path(spec_path).resolve()
    output_dir = Path(output_dir).resolve()
    data = json.loads(spec_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or set(data) != {'schema','entries'} or data['schema'] != 1:
        raise ValueError('expected JSON object with schema:1 and entries')
    entries = data['entries']
    if not isinstance(entries,list) or not 1 <= len(entries) <= MAX_ENTRIES:
        raise ValueError('requires 1..8 texture entries')
    if output_dir.exists():
        raise ValueError('output directory already exists; refusing to overwrite')
    prepared = []
    ids, locators = set(), []
    for item in entries:
        if not isinstance(item,dict) or set(item) != {'id','capture','image'}:
            raise ValueError('each entry needs id, capture and image')
        name = item['id']
        if not isinstance(name,str) or not SLUG.fullmatch(name) or name in ids:
            raise ValueError('invalid/duplicate entry id')
        ids.add(name)
        if not all(isinstance(item[k],str) and item[k] for k in ('capture','image')):
            raise ValueError('invalid input paths')
        capture = (spec_path.parent / item['capture']).resolve()
        image = (spec_path.parent / item['image']).resolve()
        meta = json.loads(capture.read_text(encoding='utf-8'))
        if not all(k in meta for k in (*texture_sample.FIELDS[:9],
                                     'source_words','palette_words','source_sha256')):
            raise ValueError('capture lacks exact source/CLUT identity')
        words, palette = meta['source_words'], meta['palette_words']
        if not isinstance(words,list) or not isinstance(palette,list) or not all(
                type(x) is int and 0 <= x <= 65535 for x in words + palette):
            raise ValueError('bad 16-bit reference data')
        digest = hashlib.sha256(struct.pack('<'+str(len(words)+len(palette))+'H',
                                             *words,*palette)).hexdigest()
        if digest != meta['source_sha256']:
            raise ValueError('source fingerprint mismatch')
        locator = tuple(meta[k] for k in ('depth','page_x','page_y','cx','cy'))
        rect = (meta['u'], meta['v'], meta['u']+meta['w'], meta['v']+meta['h'])
        for previous_locator, previous_rect in locators:
            if locator == previous_locator and (
                rect[0] < previous_rect[2] and previous_rect[0] < rect[2] and
                rect[1] < previous_rect[3] and previous_rect[1] < rect[3]
            ):
                raise ValueError('overlapping UV regions on the same texture page/CLUT')
        locators.append((locator, rect))
        from PIL import Image
        with Image.open(image) as picture:
            if 'A' in picture.getbands() and picture.getchannel('A').getextrema() != (255,255):
                raise ValueError('replacement PNG must be opaque; cutout remains PS1-owned')
            rgb = picture.convert('RGB')
            m = {k:meta[k] for k in texture_sample.FIELDS[:9]}
            m.update(iw=rgb.width,ih=rgb.height)
            binary = texture_sample.build(m,words,palette,rgb.tobytes())
        prepared.append((name,binary,m))
    output_dir.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='ttkhd-',dir=output_dir.parent) as tmp:
        stage = Path(tmp)
        for name,binary,_ in prepared:
            (stage/(name+'.ttktex')).write_bytes(binary)
        (stage/'pack.ttkpack').write_text(
            'TTKPACK1\n'+'\n'.join(name+'.ttktex' for name,_,_ in prepared)+'\n',
            encoding='ascii',newline='\n')
        stage.rename(output_dir)
    return prepared

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path,help='local JSON that names D16 captures and PNG files')
    p.add_argument('output',type=Path,help='new output directory')
    a=p.parse_args(argv)
    try: prepared=compile_pack(a.manifest,a.output)
    except (OSError,ValueError,TypeError,KeyError) as exc: p.error(str(exc))
    for name,_,m in prepared:
        print(f'{name}: {m["w"]}x{m["h"]} -> {m["iw"]}x{m["ih"]}')
    print('Pack manifest:',a.output/'pack.ttkpack')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
