"""Shared drawing helpers for the Review 0 poster and deck (python-pptx). Palette taken from the TCE Project III template."""
import os
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

NAVY, DEEP, AMBER, GREEN, LIGHT, INK, MUTED = '1F3A5F', '0F2240', 'E09B1A', '2E7D5B', 'EEF3F9', '222B38', '5A6675'
SUN, RED, TEAL, WHITE, LINE, PALEGREEN = 'F2C86B', 'C0392B', '1A8F8F', 'FFFFFF', 'C9D6E6', 'E6F2EC'
FONT = 'Calibri'
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
IMG2 = os.path.join(HERE, '_img2'); RES = os.path.join(ROOT, 'Review0_Prototype_Demo', 'results'); P10 = os.path.join(ROOT, 'Proof', '10_Review0_Sensors_and_Panels')
def rgb(h): return RGBColor.from_string(h)

class Canvas:
    """unit = 'mm' (poster) or 'in' (deck); all coordinates are given in that unit"""
    def __init__(self, slide, unit):
        self.s = slide; self.k = 36000 if unit == 'mm' else 914400
    def e(self, v): return int(round(v * self.k))

    def rect(self, x, y, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.RECTANGLE, radius=None, alpha=None):
        sh = self.s.shapes.add_shape(shape, self.e(x), self.e(y), self.e(w), self.e(h))
        if fill: sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
        else: sh.fill.background()
        if line: sh.line.color.rgb = rgb(line); sh.line.width = Pt(lw)
        else: sh.line.fill.background()
        if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = radius
        if alpha is not None and fill:
            clr = sh.fill._xPr.find(qn('a:solidFill')).find(qn('a:srgbClr')); a = etree.SubElement(clr, qn('a:alpha')); a.set('val', str(int(alpha * 100000)))
        sh.shadow.inherit = False
        return sh

    def gradient(self, x, y, w, h, c1, c2, angle=0):
        sh = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, self.e(x), self.e(y), self.e(w), self.e(h)); sh.line.fill.background(); sh.shadow.inherit = False
        sh.fill.gradient(); sh.fill.gradient_angle = angle
        st = sh.fill.gradient_stops; st[0].color.rgb = rgb(c1); st[0].position = 0; st[1].color.rgb = rgb(c2); st[1].position = 1
        return sh

    def text(self, x, y, w, h, runs, size=12, color=INK, bold=False, align='l', anchor='t', italic=False, spacing=None, margin=0.0, line=None):
        """runs: str | list of paragraphs; a paragraph is str | list of (text, {bold,color,size,italic}) tuples"""
        tb = self.s.shapes.add_textbox(self.e(x), self.e(y), self.e(w), self.e(h)); tf = tb.text_frame; tf.word_wrap = True
        m = self.e(margin); tf.margin_left = tf.margin_right = m; tf.margin_top = tf.margin_bottom = m
        tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
        paras = runs if isinstance(runs, list) else [runs]
        for i, pr in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[align]
            if spacing is not None: p.space_after = Pt(spacing)
            if line is not None: p.line_spacing = line
            parts = pr if isinstance(pr, list) else [(pr, {})]
            for t, o in parts:
                r = p.add_run(); r.text = t; f = r.font; f.name = FONT; f.size = Pt(o.get('size', size)); f.bold = o.get('bold', bold); f.italic = o.get('italic', italic); f.color.rgb = rgb(o.get('color', color))
        return tb

    def pic(self, path, x, y, w=None, h=None, border=None):
        from PIL import Image
        im = Image.open(path); ar = im.size[1] / im.size[0]
        if w is not None and h is None: h = w * ar
        elif h is not None and w is None: w = h / ar
        pc = self.s.shapes.add_picture(path, self.e(x), self.e(y), self.e(w), self.e(h))
        if border: pc.line.color.rgb = rgb(border); pc.line.width = Pt(1)
        return pc, w, h

def new_pres(w_emu, h_emu):
    p = Presentation(); p.slide_width = Emu(w_emu); p.slide_height = Emu(h_emu); return p
def blank(p): return p.slides.add_slide(p.slide_layouts[6])
