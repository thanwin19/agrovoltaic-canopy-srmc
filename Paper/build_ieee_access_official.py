# -*- coding: utf-8 -*-
"""Fills the OFFICIAL IEEE Access Word template (Access-Template-2024.docx, downloaded from ieeeaccess.ieee.org) with the project paper.
All formatting comes from the template's own styles (Paper Title, AU, PI, Abstract, IT, H1_List, H2_Cont, PARA, Equation, Fig Caption, Table Title, References, AU_Bios).
python build_ieee_access_official.py"""
import os, re, sys
os.environ['PROJECT'] = '1'
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import paper_text as T
from build_publisher_versions import add_marked, AUTHORS
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', '_official_templates', 'IEEE_Access_Template_2024.docx'))
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

def clear(p):
    for r in list(p._p):
        if r.tag != qn('w:pPr'): p._p.remove(r)
def set_text(p, parts):
    clear(p)
    for t, b, sup in parts:
        r = p.add_run(t); r.bold = b or None; r.font.superscript = sup or None

def build(out):
    d = Document(TEMPLATE); body = d.element.body; kids = list(body)
    for k in kids[12:-1]: body.remove(k)                                   # remove the template's sample text, keep the front matter and the final two-column section
    P = d.paragraphs
    set_text(P[2], [(T.TITLE, False, False)])
    n = len(AUTHORS)
    parts = []
    for i, a in enumerate(AUTHORS):
        parts.append((a, False, False)); parts.append(('1', False, True)); parts.append((', ' if i < n - 2 else (', and ' if i == n - 2 else ''), False, False))
    set_text(P[3], parts)
    set_text(P[4], [('1', False, True), ('Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai 625 015, India', False, False)])
    for idx in (6, 5): P[idx]._p.getparent().remove(P[idx]._p)
    P = d.paragraphs
    set_text(P[5], [('Corresponding author: [corresponding author name] (e-mail: [e-mail]).', False, False)])
    set_text(P[6], [('[Funding and acknowledgement of support: to be completed by the authors.]', False, False)])
    ab = T.ABSTRACT.replace('Abstract - ', '', 1)
    p = P[7]; clear(p); r = p.add_run('ABSTRACT'); r.bold = True; p.add_run(' ' + ab)
    p = P[8]; clear(p); r = p.add_run('INDEX TERMS'); r.bold = True; p.add_run(' ' + ', '.join(sorted(['agrovoltaics', 'co-optimization', 'crop light', 'sensor-based tilt control', 'solar tracking', 'simulation'])) + '.')
    first_h1 = [True]; after_h1 = [False]; fig_n = [0]; tab_n = [0]; prev_h2 = [False]
    def para(text, style='PARA'):
        q = d.add_paragraph(style=style); add_marked(q, text); return q
    for it in T.BODY:
        k = it[0]
        if k == 'h1':
            if it[1] == 'Data Availability': continue
            q = d.add_paragraph(style='H1_List (No Space)' if first_h1[0] else 'H1_List (Space)'); q.add_run(it[1].upper()); first_h1[0] = False; after_h1[0] = True; prev_h2[0] = False
        elif k == 'h2':
            q = d.add_paragraph(style='H2_First' if after_h1[0] else 'H2_Cont'); q.add_run(re.sub(r'^[IVX]+\.\s+', '', it[1]).upper()); after_h1[0] = True
        elif k == 'p':
            if it[1].startswith('The simulation code, data files'): continue
            para(it[1], 'PARA' if after_h1[0] else 'PARA_Indent'); after_h1[0] = False
        elif k == 'bul':
            para('•  ' + it[1], 'PARA_Indent'); after_h1[0] = False
        elif k == 'eq':
            q = d.add_paragraph(style='Equation'); q.add_run('\t'); add_marked(q, it[1]); q.add_run('\t(%s)' % it[2]); after_h1[0] = False
        elif k == 'fig':
            fig_n[0] += 1; q = d.add_paragraph(style='Figure Caption'); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; q.add_run().add_picture(os.path.join(HERE, 'figures', it[1]), width=Inches(min(3.4, it[2])))
            c = d.add_paragraph(style='Fig Caption'); add_marked(c, '%s. %s' % (it[3], it[4])); after_h1[0] = False
        elif k == 'tab':
            tab_n[0] += 1; q = d.add_paragraph(style='Table Title'); q.add_run('TABLE %s' % ROMAN[tab_n[0] - 1]); q2 = d.add_paragraph(style='Table Title'); add_marked(q2, it[1])
            heads, rows, widths = it[2], it[3], it[4]; tb = d.add_table(rows=1, cols=len(heads)); tot = float(sum(widths))
            tblPr = tb._tbl.tblPr; bd = OxmlElement('w:tblBorders')
            for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
                e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:space'), '0'); e.set(qn('w:color'), 'auto'); bd.append(e)
            tblPr.append(bd)
            for j, h in enumerate(heads):
                cell = tb.rows[0].cells[j]; cell.text = ''; add_marked(cell.paragraphs[0], h, size=8, bold=True); cell.width = Inches(3.4 * widths[j] / tot)
            for r in rows:
                cells = tb.add_row().cells
                for j, v in enumerate(r): cells[j].text = ''; add_marked(cells[j].paragraphs[0], v, size=8); cells[j].width = Inches(3.4 * widths[j] / tot)
            for row in tb.rows:
                for cell in row.cells:
                    for pp in cell.paragraphs: pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.space_before = Pt(0)
            d.add_paragraph(style='PARA'); after_h1[0] = False
    d.add_paragraph(style='H1').add_run('DATA AVAILABILITY')
    para('The simulation code, data files, and result tables are available at https://github.com/thanwin19/agrovoltaic-canopy-srmc. The weather data are public (NASA POWER, PVGIS).', 'PARA')
    d.add_paragraph(style='H1').add_run('REFERENCES')
    for ref in T.REFS:
        q = d.add_paragraph(style='References'); add_marked(q, ref)
    bios = [(a.upper(), ' is a final-year student in the Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai, India. [Add degrees, research interests, publications and a photograph, 25.4 mm by 31.8 mm.]') for a in AUTHORS[:4]]
    bios.append(('M. MEENAKSHI DEVI', ' is an Assistant Professor in the Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai, India. [Add degrees, research interests, publications and a photograph.]'))
    for name, txt in bios:
        q = d.add_paragraph(style='AU_Bios'); r = q.add_run(name); r.bold = True; q.add_run(txt)
    d.core_properties.title = T.TITLE; d.core_properties.author = ''; d.core_properties.last_modified_by = ''
    d.save(out); return out
if __name__ == '__main__':
    o = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', 'IEEE', 'IEEE_Access', 'SRMC_Manuscript_IEEE_Access.docx')); print(build(o))
