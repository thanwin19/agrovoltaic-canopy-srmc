# -*- coding: utf-8 -*-
"""Fills the Springer Nature Word template (SpringerNature_Word_Template.docx; the copy found on a conference website, confirm against the official download) with the project paper,
using the template's own styles (Title, Heading 3 for authors, Heading 1/2, Body Text).   python build_springer_nature_official.py"""
import os, re
os.environ['PROJECT'] = '1'
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import paper_text as T
from build_publisher_versions import add_marked, AUTHORS, KEYWORDS
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', '_official_templates', 'SpringerNature_Word_Template.docx'))

def build(out):
    d = Document(TEMPLATE); body = d.element.body; kids = list(body)
    for k in kids[:-1]: body.remove(k)                                      # drop the template's instructions, keep its page setup
    SM = {st.name: st for st in d.styles}
    S = lambda n: SM[n]
    def P(style, text='', bold=False, align=None):
        q = d.add_paragraph(style=S(style)); add_marked(q, text, bold=bold)
        if align == 'j': q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return q
    P('Title', T.TITLE)
    q = d.add_paragraph(style=S('Normal')); r = q.add_run(', '.join(a + ('*' if i == 0 else '') for i, a in enumerate(AUTHORS))); r.bold = True; r.font.size = Pt(12)
    P('Normal', 'Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai 625 015, India.')
    P('Normal', '*Corresponding author: [name, e-mail]. Contributing authors: [e-mail of each author]. ORCID: [to be completed].')
    q = d.add_paragraph(style=S('Body Text')); r = q.add_run('Abstract '); r.bold = True; add_marked(q, T.ABSTRACT.replace('Abstract - ', '', 1)); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    q = d.add_paragraph(style=S('Body Text')); r = q.add_run('Keywords '); r.bold = True; q.add_run(', '.join(KEYWORDS))
    h1 = h2 = 0; fig_n = tab_n = 0
    for it in T.BODY:
        k = it[0]
        if k == 'h1':
            if it[1] == 'Data Availability': continue
            h1 += 1; h2 = 0; d.add_paragraph(style=S('Heading 1')).add_run('%d  %s' % (h1, it[1]))
        elif k == 'h2':
            h2 += 1; d.add_paragraph(style=S('Heading 2')).add_run('%d.%d  %s' % (h1, h2, re.sub(r'^[IVX]+\.\s+', '', it[1])))
        elif k == 'p':
            if it[1].startswith('The simulation code, data files'): continue
            P('Body Text', it[1], align='j')
        elif k == 'bul':
            P('List Paragraph', '•  ' + it[1])
        elif k == 'eq':
            q = d.add_paragraph(style=S('Body Text')); q.paragraph_format.tab_stops.add_tab_stop(Inches(3.0), alignment=1); q.paragraph_format.tab_stops.add_tab_stop(Inches(6.0), alignment=2); q.add_run('\t'); add_marked(q, it[1]); q.add_run('\t(%s)' % it[2])
        elif k == 'fig':
            fig_n += 1; q = d.add_paragraph(style=S('Normal')); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; q.add_run().add_picture(os.path.join(HERE, 'figures', it[1]), width=Inches(min(5.2, it[2] * 1.6)))
            c = d.add_paragraph(style=S('Normal')); r = c.add_run('Fig. %d ' % fig_n); r.bold = True; add_marked(c, '%s. %s' % (it[3], it[4]), size=9)
        elif k == 'tab':
            tab_n += 1; c = d.add_paragraph(style=S('Normal')); r = c.add_run('Table %d ' % tab_n); r.bold = True; add_marked(c, it[1], size=9)
            heads, rows, widths = it[2], it[3], it[4]; tb = d.add_table(rows=1, cols=len(heads)); tot = float(sum(widths)); tblPr = tb._tbl.tblPr; bd = OxmlElement('w:tblBorders')
            for side in ('top', 'bottom', 'insideH'):
                e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:space'), '0'); e.set(qn('w:color'), 'auto'); bd.append(e)
            tblPr.append(bd)
            for j, h in enumerate(heads): cell = tb.rows[0].cells[j]; cell.text = ''; add_marked(cell.paragraphs[0], h, size=9, bold=True); cell.width = Inches(5.5 * widths[j] / tot)
            for rr in rows:
                cells = tb.add_row().cells
                for j, v in enumerate(rr): cells[j].text = ''; add_marked(cells[j].paragraphs[0], v, size=9); cells[j].width = Inches(5.5 * widths[j] / tot)
            d.add_paragraph(style=S('Body Text'))
    d.add_paragraph(style=S('Heading 1')).add_run('Declarations')
    for t in ('Funding: [to be completed by the authors].', 'Competing interests: [to be completed by the authors].', 'Data availability: the simulation code, data files, and result tables are available at https://github.com/thanwin19/agrovoltaic-canopy-srmc. The weather data are public (NASA POWER, PVGIS).', 'Author contribution: [to be completed by the authors].'):
        P('Body Text', t)
    d.add_paragraph(style=S('Heading 1')).add_run('References')
    for i, ref in enumerate(T.REFS, 1):
        q = d.add_paragraph(style=S('Normal')); add_marked(q, '%d. %s' % (i, ref), size=9)
    d.core_properties.title = T.TITLE; d.core_properties.author = ''; d.core_properties.last_modified_by = ''
    d.save(out); return out
if __name__ == '__main__':
    o = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', 'Springer_Nature', 'Energy_Sustainability_and_Society', 'SRMC_Manuscript_Energy_Sustainability_and_Society.docx')); print(build(o))
