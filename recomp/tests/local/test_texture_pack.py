"""Synthetic HD pack tests, including native C parsing; no disc data needed."""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/local'))
import texture_pack

class TexturePackTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p=Path(self.temp.name)
    def fixture(self,name,px=640, u=0, v=16):
        from PIL import Image
        words=[0x1234]*16
        palette=list(range(16))
        raw=struct.pack('<32H',*words,*palette)
        m={'depth':0,'page_x':px,'page_y':0,'u':u,'v':v,'w':8,'h':8,
           'cx':0,'cy':300,'source_words':words,'palette_words':palette,
           'source_sha256':hashlib.sha256(raw).hexdigest()}
        (self.p/f'{name}.json').write_text(json.dumps(m))
        Image.new('RGB',(16,16),(80,120,160)).save(self.p/f'{name}.png')
        return {'id':name,'capture':name+'.json','image':name+'.png'}
    def manifest(self,items):
        p=self.p/'spec.json'
        p.write_text(json.dumps({'schema':1,'entries':items}))
        return p
    def test_two_textures_and_native_loader(self):
        items=[self.fixture('wall_a',640),self.fixture('wall_b',704)]
        texture_pack.compile_pack(self.manifest(items),self.p/'pack')
        self.assertEqual((self.p/'pack/pack.ttkpack').read_text(),
                         'TTKPACK1\nwall_a.ttktex\nwall_b.ttktex\n')
        hdr=ROOT/'psxrecomp/runtime/src'
        if not shutil.which('cc') or not (hdr/'ttk_texture_pack.h').is_file():
            return
        (self.p/'probe.c').write_text(
            '#include "ttk_texture_pack.h"\n#include <assert.h>\n'
            'int main(int argc,char **argv){(void)argc;TtkHdPack p={0};'
            'assert(ttk_hd_pack_load(argv[1],&p));assert(p.count==2);'
            'ttk_hd_pack_free(&p);return 0;}\n')
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                        '-Wno-unused-function','-I',str(hdr),
                        str(self.p/'probe.c'),'-o',str(self.p/'probe')],check=True)
        subprocess.run([str(self.p/'probe'),str(self.p/'pack/pack.ttkpack')],check=True)
    def test_same_page_different_uv_regions_accepted(self):
        items=[self.fixture('wall_a',u=0),self.fixture('wall_b',u=8)]
        texture_pack.compile_pack(self.manifest(items),self.p/'pack')
        self.assertEqual((self.p/'pack/pack.ttkpack').read_text(),
                         'TTKPACK1\\nwall_a.ttktex\\nwall_b.ttktex\\n'.replace('\\n','\n'))
        hdr=ROOT/'psxrecomp/runtime/src'
        if not shutil.which('cc') or not (hdr/'ttk_texture_pack.h').is_file():
            return
        (self.p/'probe.c').write_text(
            '#include "ttk_texture_pack.h"\n#include <assert.h>\n'
            'int main(int argc,char **argv){(void)argc;TtkHdPack p={0};'
            'assert(ttk_hd_pack_load(argv[1],&p));assert(p.count==2);'
            'assert(ttk_hd_uv_contains(&p.sample[0],0,16,8,24));'
            'assert(!ttk_hd_uv_contains(&p.sample[0],0,16,9,24));'
            'assert(ttk_hd_uv_contains(&p.sample[1],8,16,16,24));'
            'assert(!ttk_hd_uv_contains(&p.sample[1],7,16,16,24));'
            'ttk_hd_pack_free(&p);return 0;}\n')
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',
                        '-Wno-unused-function','-I',str(hdr),
                        str(self.p/'probe.c'),'-o',str(self.p/'probe')],check=True)
        subprocess.run([str(self.p/'probe'),str(self.p/'pack/pack.ttkpack')],check=True)

    def test_overlapping_same_page_rejected(self):
        items=[self.fixture('wall_a',u=0),self.fixture('wall_b',u=4)]
        with self.assertRaisesRegex(ValueError,'overlapping UV'):
            texture_pack.compile_pack(self.manifest(items),self.p/'pack')
        self.assertFalse((self.p/'pack').exists())

    def test_different_palette_can_reuse_same_uv(self):
        a=self.fixture('wall_a')
        b=self.fixture('wall_b')
        path=self.p/'wall_b.json'
        m=json.loads(path.read_text())
        m['cx']=16
        path.write_text(json.dumps(m))
        texture_pack.compile_pack(self.manifest([a,b]),self.p/'pack')
        self.assertTrue((self.p/'pack/pack.ttkpack').exists())
    def test_changed_source_hash_refused(self):
        item=self.fixture('wall')
        path=self.p/'wall.json'
        meta=json.loads(path.read_text());meta['source_sha256']='0'*64
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            texture_pack.compile_pack(self.manifest([item]),self.p/'pack')
        self.assertFalse((self.p/'pack').exists())
    def test_invalid_id_and_duplicate_id(self):
        item=self.fixture('wall')
        with self.assertRaises(ValueError):
            texture_pack.compile_pack(self.manifest([item,item]),self.p/'pack')
        item['id']='../bad'
        with self.assertRaises(ValueError):
            texture_pack.compile_pack(self.manifest([item]),self.p/'pack')

if __name__=='__main__':
    unittest.main()
