# -*- coding: utf-8 -*-
"""Builds the paper in the general manuscript style of five publishers (same text, different front matter, numbering, spacing and back matter).
Output: publisher_versions/SRMC_Paper_<Publisher>.docx (+ pdf via LibreOffice).   python build_publisher_versions.py
IMPORTANT: these follow each publisher's published general instructions, not the official journal template; before submission, download the template of the chosen journal."""
import os, re, shutil
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
os.environ['PROJECT'] = '1'          # the publisher versions are the project paper (reviews 0-5, month run, prototype photo)
import paper_text as T

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'publisher_versions'); os.makedirs(OUT, exist_ok=True)
REPO = 'https://github.com/thanwin19/agrovoltaic-canopy-srmc'
AUTHORS = ['Thanwin S S', 'Chandru P M', 'Kuberaeshwaran S', 'Mukilan A', 'M. Meenakshi Devi']
AFF = 'Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai 625 015, India'
KEYWORDS = ['agrovoltaics', 'co-optimization', 'crop light', 'sensor-based tilt control', 'solar tracking', 'simulation']
HIGHLIGHTS = ['Six-sensor tilt controller co-optimizes crop light and electricity', 'Accuracy is scored against the best possible tilt: 99.6 % at seven climates', 'A fixed 45° tilt reaches 91.2 % and a monthly plan 98.8 %', 'Datasheet-sized sensor errors cost the controller little accuracy', 'One motor and a lever arm on each row tilt all rows by the same angle']
PUBS = {
 'Elsevier': dict(font='Times New Roman', size=12, spacing=1.5, numbered=True, fig='Fig.', tabpos='above', lines=True, highlights=True, cols=1, kw_sep='; ', kw_label='Keywords: ',
                  back=[('Declaration of competing interest', '[To be completed by the authors.]'), ('CRediT authorship contribution statement', '[To be completed by the authors: each author\'s contribution using the CRediT roles.]'), ('Funding', '[To be completed by the authors. State "none" if there was no funding.]'), ('Data availability', 'The simulation code, data files, and result tables are available at ' + REPO + '. The weather data are public (NASA POWER, PVGIS).'), ('Acknowledgements', '[Optional.]')]),
 'Springer Nature': dict(font='Times New Roman', size=11, spacing=1.5, numbered=True, fig='Fig.', tabpos='above', lines=False, highlights=False, cols=1, kw_sep=', ', kw_label='Keywords: ',
                  back=[('Declarations', None), ('Funding', '[To be completed by the authors.]'), ('Competing interests', '[To be completed by the authors.]'), ('Data availability', 'The simulation code, data files, and result tables are available at ' + REPO + '. The weather data are public (NASA POWER, PVGIS).'), ('Author contribution', '[To be completed by the authors.]')]),
 'Taylor and Francis': dict(font='Times New Roman', size=12, spacing=2.0, numbered=True, fig='Figure', tabpos='above', lines=False, highlights=False, cols=1, kw_sep=', ', kw_label='KEYWORDS ',
                  back=[('Disclosure statement', '[To be completed by the authors. State any potential conflict of interest, or that there is none.]'), ('Funding', '[To be completed by the authors.]'), ('Data availability statement', 'The simulation code, data files, and result tables are openly available at ' + REPO + '. The weather data are public (NASA POWER, PVGIS).')]),
 'MDPI': dict(font='Palatino Linotype', size=10, spacing=1.0, numbered=True, fig='Figure', tabpos='above', lines=False, highlights=False, cols=1, kw_sep='; ', kw_label='Keywords: ',
                  back=[('Author Contributions', '[To be completed by the authors, for example: Conceptualization, ...; methodology, ...; software, ...; writing, ...]'), ('Funding', '[To be completed by the authors.]'), ('Institutional Review Board Statement', 'Not applicable.'), ('Informed Consent Statement', 'Not applicable.'), ('Data Availability Statement', 'The simulation code, data files, and result tables are available at ' + REPO + '. The weather data are public (NASA POWER, PVGIS).'), ('Acknowledgments', '[Optional.]'), ('Conflicts of Interest', '[To be completed by the authors.]')]),
}
TOK = re.compile(r'(</?(?:i|b|sub|sup)>)')
def add_marked(par, text, size=None, bold=False, italic=False):
    st = {'i': italic, 'b': bold, 'sub': False, 'sup': False}
    for tok in TOK.split(text):
        m = re.fullmatch(r'<(/?)(i|b|sub|sup)>', tok)
        if m: st[m.group(2)] = not m.group(1); continue
        if not tok: continue
        r = par.add_run(tok); r.italic = st['i'] or None; r.bold = st['b'] or None; r.font.subscript = st['sub'] or None; r.font.superscript = st['sup'] or None
        if size: r.font.size = Pt(size)

def build(name, cfg):
    d = Document(); sec = d.sections[0]; sec.left_margin = sec.right_margin = Cm(2.5); sec.top_margin = sec.bottom_margin = Cm(2.5)
    if cfg['lines']:
        ln = OxmlElement('w:lnNumType'); ln.set(qn('w:countBy'), '1'); ln.set(qn('w:restart'), 'continuous'); sec._sectPr.append(ln)
    stn = d.styles['Normal']; stn.font.name = cfg['font']; stn.font.size = Pt(cfg['size']); stn.element.rPr.rFonts.set(qn('w:eastAsia'), cfg['font'])
    stn.paragraph_format.line_spacing = cfg['spacing']; stn.paragraph_format.space_after = Pt(6)
    for h, sz in (('Heading 1', cfg['size'] + 2), ('Heading 2', cfg['size'] + 1)):
        hs = d.styles[h]; hs.font.name = cfg['font']; hs.font.size = Pt(sz); hs.font.bold = True; hs.font.color.rgb = RGBColor(0, 0, 0); hs.element.rPr.rFonts.set(qn('w:ascii'), cfg['font']); hs.element.rPr.rFonts.set(qn('w:hAnsi'), cfg['font'])
        hs.paragraph_format.space_before = Pt(12); hs.paragraph_format.space_after = Pt(6); hs.paragraph_format.keep_with_next = True
    d.styles['Heading 2'].font.italic = True
    def para(text='', align=None, bold=False, italic=False, size=None, after=None):
        p = d.add_paragraph(); add_marked(p, text, size=size, bold=bold, italic=italic)
        if align == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if align == 'j': p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if after is not None: p.paragraph_format.space_after = Pt(after)
        return p
    # ---- front matter
    para(T.TITLE, align='c', bold=True, size=cfg['size'] + 6, after=10)
    para(', '.join(AUTHORS) + '*', align='c', size=cfg['size'] + 1, after=2); para(AFF, align='c', italic=True, size=cfg['size'] - 1, after=2)
    para('*Corresponding author: [corresponding author name and e-mail]   |   [ORCID of each author]', align='c', size=cfg['size'] - 2, after=10)
    if cfg['highlights']:
        para('Highlights', bold=True, after=2)
        for h in HIGHLIGHTS: d.add_paragraph(h, style='List Bullet')
    ab = T.ABSTRACT.replace('Abstract - ', '', 1); para('Abstract', bold=True, after=2); para(ab, align='j')
    para(cfg['kw_label'] + cfg['kw_sep'].join(KEYWORDS), italic=False, after=10)
    # ---- body
    h1n = [0]; h2n = [0]; fig_n = [0]; tab_n = [0]; scale = 1.75
    for it in T.BODY:
        k = it[0]
        if k == 'h1':
            if it[1] == 'Data Availability': continue
            h1n[0] += 1; h2n[0] = 0; d.add_heading(('%d. %s' % (h1n[0], it[1])) if cfg['numbered'] else it[1], 1)
        elif k == 'h2':
            h2n[0] += 1; t = re.sub(r'^[IVX]+\.\s+', '', it[1]); d.add_heading(('%d.%d %s' % (h1n[0], h2n[0], t)) if cfg['numbered'] else t, 2)
        elif k == 'p':
            if it[1].startswith('The simulation code, data files'): continue
            para(it[1], align='j')
        elif k == 'bul':
            p = d.add_paragraph(style='List Bullet'); add_marked(p, it[1])
        elif k == 'eq':
            p = d.add_paragraph(); p.paragraph_format.tab_stops.add_tab_stop(Cm(8.0), alignment=1); p.paragraph_format.tab_stops.add_tab_stop(Cm(16.0), alignment=2); p.add_run('\t'); add_marked(p, it[1]); p.add_run('\t(%s)' % it[2])
        elif k == 'fig':
            fig_n[0] += 1; p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(os.path.join(HERE, 'figures', it[1]), width=Inches(min(5.8, it[2] * scale)))
            c = d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; add_marked(c, '%s %d. %s. %s' % (cfg['fig'], fig_n[0], it[2 + 1], it[2 + 2]), size=cfg['size'] - 1)
        elif k == 'tab':
            tab_n[0] += 1; c = d.add_paragraph(); add_marked(c, 'Table %d. %s' % (tab_n[0], it[1]), size=cfg['size'] - 1, bold=True); c.paragraph_format.keep_with_next = True
            heads, rows, widths = it[2], it[3], it[4]; tb = d.add_table(rows=1, cols=len(heads)); tb.style = 'Table Grid'; tb.alignment = WD_TABLE_ALIGNMENT.CENTER
            tot = float(sum(widths))
            for j, h in enumerate(heads):
                cell = tb.rows[0].cells[j]; cell.text = ''; add_marked(cell.paragraphs[0], h, size=cfg['size'] - 1, bold=True); cell.width = Inches(6.0 * widths[j] / tot)
            for r in rows:
                cells = tb.add_row().cells
                for j, v in enumerate(r): cells[j].text = ''; add_marked(cells[j].paragraphs[0], v, size=cfg['size'] - 1); cells[j].width = Inches(6.0 * widths[j] / tot)
            for row in tb.rows:
                for cell in row.cells:
                    for pp in cell.paragraphs: pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.line_spacing = 1.0
            d.add_paragraph()
    # ---- back matter
    for title, txt in cfg['back']:
        d.add_heading(title, 1)
        if txt: para(txt, align='j')
    d.add_heading('References', 1)
    for i, ref in enumerate(T.REFS, 1):
        p = d.add_paragraph(); add_marked(p, '[%d] %s' % (i, ref), size=cfg['size'] - 1); p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.9); p.paragraph_format.line_spacing = 1.0; p.paragraph_format.space_after = Pt(3)
    d.core_properties.title = T.TITLE; d.core_properties.author = ''; d.core_properties.last_modified_by = ''
    out = os.path.join(OUT, 'SRMC_Paper_%s.docx' % name.replace(' ', '_')); d.save(out); print('saved', out); return out
for n, c in PUBS.items(): build(n, c)
shutil.copy(os.path.join(HERE, 'SRMC_Research_Paper.docx'), os.path.join(OUT, 'SRMC_Paper_IEEE.docx')); print('IEEE = the two-column IEEE-style build (ProComm template)')
