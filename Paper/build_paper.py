# -*- coding: utf-8 -*-
"""Builds the paper in the ProComm template (DOC-20260803-WA0032.docx).   python build_paper.py
Output: SRMC_Research_Paper.docx (template styles, two columns, no page numbers, no comments, no hyperlinks)."""
import os, re, copy
from docx import Document
from docx.shared import Pt, Inches, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import paper_text as T

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'DOC-20260803-WA0032.docx'); OUT = os.path.join(HERE, 'SRMC_Research_Paper.docx')
doc = Document(TEMPLATE); body = doc.element.body; kids = list(body)
# ------------------------------------------------------------ anchors in the template
title_tbl, p_abs, p_idx, sect_par = kids[0], kids[4], kids[6], kids[97]
assert kids[7].xpath('string(.)').strip() == 'Introduction' and sect_par.find('.//' + qn('w:sectPr')) is not None
TOK = re.compile(r'(</?(?:i|b|sub|sup)>)')
def add_marked(par, text, base_italic=False):
    st = {'i': base_italic, 'b': False, 'sub': False, 'sup': False}
    for tok in TOK.split(text):
        m = re.fullmatch(r'<(/?)(i|b|sub|sup)>', tok)
        if m: st[m.group(2)] = not m.group(1); continue
        if not tok: continue
        r = par.add_run(tok)
        if st['i']: r.italic = True
        if st['b']: r.bold = True
        if st['sub']: r.font.subscript = True
        if st['sup']: r.font.superscript = True
def clear_runs(p_el):
    for ch in list(p_el):
        if ch.tag != qn('w:pPr'): p_el.remove(ch)
# ------------------------------------------------------------ title block
tt = doc.tables[0]
def set_cell(cell, text):
    ps = cell.paragraphs
    if not ps: return
    for extra in ps[1:]: extra._p.getparent().remove(extra._p)
    p = ps[0]; runs = p.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]: r._r.getparent().remove(r._r)
    else: p.add_run(text)
    for br in p._p.findall('.//' + qn('w:br')): br.getparent().remove(br)
seen = set()
for row in tt.rows:
    for c in row.cells:
        if id(c._tc) in seen: continue
        seen.add(id(c._tc))
row0, row1 = tt.rows[0], tt.rows[1]
set_cell(row0.cells[0], T.TITLE)
cells1 = []; seen1 = set()
for c in row1.cells:
    if id(c._tc) not in seen1: seen1.add(id(c._tc)); cells1.append(c)
set_cell(cells1[0], 'Author names and affiliations withheld for review')
for c in cells1[1:]: set_cell(c, '')
try:
    cells1[0].merge(cells1[-1]); [setattr(p, 'alignment', WD_ALIGN_PARAGRAPH.CENTER) for p in tt.rows[1].cells[0].paragraphs]
except Exception as e: print('merge skipped', e)
for el in title_tbl.iter(qn('w:commentRangeStart'), qn('w:commentRangeEnd'), qn('w:commentReference')): pass
for tag in ('w:commentRangeStart', 'w:commentRangeEnd', 'w:commentReference'):
    for el in list(body.iter(qn(tag))):
        par = el.getparent(); par.remove(el)
# ------------------------------------------------------------ abstract + index terms
for p_el, text in ((p_abs, T.ABSTRACT), (p_idx, T.INDEX)):
    clear_runs(p_el); r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = text; t.set(qn('xml:space'), 'preserve'); r.append(t); p_el.append(r)
# ------------------------------------------------------------ remove template instructions (keep the section-break paragraph)
rem = False
for el in kids:
    if el is kids[7]: rem = True
    if el is sect_par: break
    if rem: body.remove(el)
# ------------------------------------------------------------ builders (each returns the element, placed before the section-break paragraph)
def place(el): sect_par.addprevious(el); return el
def new_par(style=None):
    p = doc.add_paragraph(style=style); return p
def ppr_keep(p, nxt=True): p.paragraph_format.keep_with_next = nxt
fig_n = tab_n = 0
def build_h1(text): p = new_par('Heading 1'); p.add_run(text); place(p._p)
def build_h2(text): p = new_par('Heading 2'); p.add_run(text); place(p._p)
after_eq = [False]
def build_p(text):
    p = new_par('Body Text Indent'); add_marked(p, text)
    if after_eq[0]: p.paragraph_format.first_line_indent = Pt(0)
    after_eq[0] = False; place(p._p)
def build_bul(text): p = new_par('BulletList'); add_marked(p, text); place(p._p)
def build_eq(text, num):
    p = new_par('Body Text Indent'); pf = p.paragraph_format; pf.first_line_indent = Pt(0); pf.left_indent = Pt(0)
    pPr = p._p.get_or_add_pPr(); tabs = OxmlElement('w:tabs')
    for val, pos in (('center', 2340), ('right', 4680)):
        t = OxmlElement('w:tab'); t.set(qn('w:val'), val); t.set(qn('w:pos'), str(pos)); tabs.append(t)
    pPr.append(tabs); p.add_run('\t'); add_marked(p, text); p.add_run('\t(%s)' % num); place(p._p)
def build_fig(fn, width, title, cap):
    global fig_n; fig_n += 1
    p = new_par(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2); ppr_keep(p)
    r = p.add_run(); r.add_picture(os.path.join(HERE, 'figures', fn), width=Inches(width)); place(p._p)
    c = new_par('Caption'); c.add_run('Figure %d.  %s. %s' % (fig_n, title, cap)); c.paragraph_format.space_after = Pt(6); c.paragraph_format.keep_together = True; place(c._p)
def build_tab(title, heads, rows, widths):
    global tab_n; tab_n += 1
    c = new_par('Caption'); c.add_run('Table %d. %s' % (tab_n, title)); c.paragraph_format.space_before = Pt(6); c.paragraph_format.space_after = Pt(6); c.paragraph_format.keep_together = True; ppr_keep(c); place(c._p)
    tbl = OxmlElement('w:tbl'); pr = OxmlElement('w:tblPr')
    tw = OxmlElement('w:tblW'); tw.set(qn('w:w'), str(sum(widths))); tw.set(qn('w:type'), 'dxa'); pr.append(tw)
    jc = OxmlElement('w:jc'); jc.set(qn('w:val'), 'center'); pr.append(jc)
    bd = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '2'); e.set(qn('w:space'), '0'); e.set(qn('w:color'), 'auto'); bd.append(e)
    pr.append(bd); lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); pr.append(lay)
    mar = OxmlElement('w:tblCellMar')
    for side, v in (('left', 50), ('right', 50)):
        e = OxmlElement('w:' + side); e.set(qn('w:w'), str(v)); e.set(qn('w:type'), 'dxa'); mar.append(e)
    pr.append(mar); tbl.append(pr); grid = OxmlElement('w:tblGrid')
    for w in widths: g = OxmlElement('w:gridCol'); g.set(qn('w:w'), str(w)); grid.append(g)
    tbl.append(grid)
    def row(cells, head):
        tr = OxmlElement('w:tr'); trpr = OxmlElement('w:trPr'); cs = OxmlElement('w:cantSplit'); trpr.append(cs)
        if head: th = OxmlElement('w:tblHeader'); trpr.append(th)
        tr.append(trpr)
        for ci, (txt, w) in enumerate(zip(cells, widths)):
            tc = OxmlElement('w:tc'); tcp = OxmlElement('w:tcPr'); tcw = OxmlElement('w:tcW'); tcw.set(qn('w:w'), str(w)); tcw.set(qn('w:type'), 'dxa'); tcp.append(tcw)
            va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); tcp.append(va); tc.append(tcp)
            p = OxmlElement('w:p'); ppr = OxmlElement('w:pPr'); ps = OxmlElement('w:pStyle'); ps.set(qn('w:val'), 'TableHead' if head else 'Tabletext'); ppr.append(ps)
            j = OxmlElement('w:jc'); j.set(qn('w:val'), 'left' if ci == 0 else 'center'); ppr.append(j); p.append(ppr); tc.append(p); tr.append(tc)
            # runs with markup
            tmp = doc.add_paragraph(); add_marked(tmp, txt)
            for r in list(tmp._p.findall(qn('w:r'))): p.append(r)
            tmp._p.getparent().remove(tmp._p)
        return tr
    tbl.append(row(heads, True))
    for r in rows: tbl.append(row(r, False))
    trs = tbl.findall(qn('w:tr'))
    for tr in trs[:-1]:
        for pp in tr.iter(qn('w:pPr')):
            kn = OxmlElement('w:keepNext'); pp.insert(1, kn)
    place(tbl)
    sp = new_par(); sp.paragraph_format.space_after = Pt(0); sp.paragraph_format.space_before = Pt(0)
    for r in sp.runs: pass
    sz = OxmlElement('w:rPr'); sp._p.get_or_add_pPr().append(sz); sp.paragraph_format.line_spacing = Pt(6); place(sp._p)
BUILD = {'h1': build_h1, 'h2': build_h2, 'p': build_p, 'bul': build_bul, 'eq': build_eq, 'fig': build_fig, 'tab': build_tab}
for item in T.BODY: BUILD[item[0]](*item[1:])
# ------------------------------------------------------------ references and authors
build_h1('References')
for i, ref in enumerate(T.REFS, 1):
    p = new_par('Heading 3'); add_marked(p, '[%d] %s' % (i, ref)); p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(5); place(p._p)
build_h1('About the Authors')
build_p('Author information is withheld for review and will be added to the camera-ready version.')
# ------------------------------------------------------------ clean the package: comments, hyperlinks, unused pictures
used = set(re.findall(r'r:embed="(rId\d+)"', doc.element.xml))
for rid, rel in list(doc.part.rels.items()):
    t = rel.reltype
    if 'comments' in t or t.endswith('/hyperlink') or (t.endswith('/image') and rid not in used): del doc.part.rels[rid]
doc.core_properties.title = T.TITLE; doc.core_properties.author = ''; doc.core_properties.last_modified_by = ''; doc.core_properties.comments = ''; doc.core_properties.subject = ''; doc.core_properties.keywords = ''
doc.save(OUT); print('saved', OUT)
