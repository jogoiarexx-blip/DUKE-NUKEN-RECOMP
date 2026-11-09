"""Exercise the actual renderer HD UV selector without commercial PS1 inputs.

Extract just the C function from the patched renderer, compile it with the real
texture-pack header and synthetic two-region table, and assert conservative
fallback for border-crossing, wrong palette, wrapping and corrected UVs.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HdUvSelectorNativeTest(unittest.TestCase):
    def test_render_selector_real_source(self):
        cc = shutil.which('cc')
        srcdir = ROOT / 'psxrecomp/runtime/src'
        header = srcdir / 'ttk_texture_pack.h'
        renderer = srcdir / 'gpu_gl_renderer.c'
        if not cc or not header.exists() or not renderer.exists():
            self.skipTest('Requires patched PSXRecomp source and a C compiler')

        source = renderer.read_text(encoding='utf-8')
        signature = ('static int d16_match(int bx,int by,int depth,int cx,int cy,int twin,\n'
                     '                     const int *us, const int *vs) {')
        try:
            start = source.index(signature)
            end = source.index('\n}\n', start) + len('\n}')
        except ValueError as exc:
            self.fail(f'patched D16 UV selection source missing: {exc}')
        selector = source[start:end]

        prefix = r'''
#include "ttk_texture_pack.h"
#include <assert.h>
static TtkHdPack s_hd;
static signed char s_d16_valid[TTK_HD_MAX];
static unsigned long long s_d16_hits;
static int s_puv_valid;
static float s_puv_u[3], s_puv_v[3];
static void d16_validate(unsigned slot) { s_d16_valid[slot] = 1; }
'''
        main = r'''
int main(void) {
    s_hd.count = 2;
    s_hd.sample[0] = (TtkTextureSample) {
        .depth = 0, .page_x = 640, .page_y = 0,
        .cx = 0, .cy = 300, .palette_n = 16,
        .u = 0, .v = 16, .w = 8, .h = 8
    };
    s_hd.sample[1] = (TtkTextureSample) {
        .depth = 0, .page_x = 640, .page_y = 0,
        .cx = 0, .cy = 300, .palette_n = 16,
        .u = 8, .v = 16, .w = 8, .h = 8
    };
    s_d16_valid[0] = -1;
    s_d16_valid[1] = -1;
    int v[3] = {16, 24, 16};
    int first[3] = {0, 3, 8};
    int second[3] = {8, 11, 16};
    int border[3] = {6, 10, 12};
    assert(d16_match(640,0,0,0,300,0,first,v) == 1);
    assert(d16_match(640,0,0,0,300,0,second,v) == 2);
    assert(d16_match(640,0,0,0,300,0,border,v) == 0);
    assert(d16_match(640,0,0,0,300,1,first,v) == 0);
    assert(d16_match(640,0,0,0,301,0,first,v) == 0);
    assert(d16_match(704,0,0,0,300,0,first,v) == 0);
    assert(d16_match(640,0,4,0,300,0,first,v) == 0);
    s_puv_valid = 1;
    s_puv_u[0]=8.0f; s_puv_u[1]=12.0f; s_puv_u[2]=16.0f;
    s_puv_v[0]=16.0f; s_puv_v[1]=22.0f; s_puv_v[2]=24.0f;
    assert(d16_match(640,0,0,0,300,0,first,v) == 2);
    s_puv_u[0]=7.9f;
    assert(d16_match(640,0,0,0,300,0,first,v) == 0);
    assert(s_d16_hits == 3);
    return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix='ttk-hd-uv-') as d:
            folder = Path(d)
            source_file = folder / 'check.c'
            program = folder / 'check'
            source_file.write_text(prefix + '\n' + selector + '\n' + main,
                                   encoding='utf-8')
            subprocess.run([cc, '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-function', '-I', str(srcdir),
                            str(source_file), '-o', str(program)], check=True)
            subprocess.run([str(program)], check=True)


if __name__ == '__main__':
    unittest.main()
