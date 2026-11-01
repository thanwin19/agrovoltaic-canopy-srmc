# -*- coding: utf-8 -*-
"""Fills the OFFICIAL Taylor & Francis Word template (TF_Template_Word_Windows_2016.dotx, from the T&F Author Services formatting page) with the project paper,
using the template's own styles (Article title, Author names, Affiliation, Abstract, Keywords, Heading 1-2, Paragraph, New paragraph, Displayed equation, Table title, Figure caption, References).
The abstract is shortened to 100 words because the International Journal of Green Energy instructions PDF I could download asks for 'not more than 100 words' (check the current rule).   python build_tf_official.py"""
import os, re
os.environ['PROJECT'] = '1'
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import paper_text as T
from build_publisher_versions import add_marked, AUTHORS
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', '_official_templates', 'TF_template.docx'))
ABSTRACT100 = ("Agrovoltaic systems share land between crops and solar panels, but a fixed panel angle favors either the crop or the electricity. "
               "We define co-optimization accuracy as a tilt controller's objective divided by that of the best possible angle, and test a six-sensor controller in simulation at seven climates with noisy sensors. "
               "It reached 99.6 to 99.7 percent at every climate, against 98.2 to 99.2 percent for a monthly schedule and 89.1 to 91.5 percent for a fixed 45 degree tilt. "
               "A simulated month with real weather and a scaled prototype are also reported. All results are simulated.")
KEYWORDS = ['agrovoltaics', 'co-optimization', 'crop light', 'tilt control', 'simulation']

def clear(p):
    for r in list(p._p):
        if r.tag != qn('w:pPr'): p._p.remove(r)
def build(out):
    assert len(ABSTRACT100.split()) <= 100, len(ABSTRACT100.split())
    d = Document(TEMPLATE); body = d.element.body
    for k in list(body)[:-1]: body.remove(k)
    SM = {s.name: s for s in d.styles}
    def P(style, text='', bold_lead=None):
        q = d.add_paragraph(style=SM[style])
        if bold_lead: q.add_run(bold_lead).bold = True
        add_marked(q, text); return q
    P('Article title', T.TITLE)
    q = d.add_paragraph(style=SM['Author names'])
    for i, a in enumerate(AUTHORS):
        q.add_run(a); q.add_run('a' + ('*' if i == 0 else '')).font.superscript = True; q.add_run(', ' if i < len(AUTHORS) - 2 else (' and ' if i == len(AUTHORS) - 2 else ''))
    P('Affiliation', 'a Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai, India')
    P('Correspondence details', '*CONTACT [corresponding author name] [e-mail]')
    P('Notes on contributors', 'Thanwin S S, Chandru P M, Kuberaeshwaran S and Mukilan A are final-year students and M. Meenakshi Devi is an Assistant Professor in the Department of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai, India. [Add degrees, interests and ORCID of each author if the journal requires notes.]')
    P('Article title', T.TITLE)
    P('Abstract', ABSTRACT100); P('Keywords', 'Keywords: ' + '; '.join(KEYWORDS))
    h1 = h2 = fig_n = tab_n = 0; first = True
    for it in T.BODY:
        k = it[0]
        if k == 'h1':
            if it[1] == 'Data Availability': continue
            h1 += 1; h2 = 0; P('Heading 1', '%d. %s' % (h1, it[1])); first = True
        elif k == 'h2':
            h2 += 1; P('Heading 2', '%d.%d. %s' % (h1, h2, re.sub(r'^[IVX]+\.\s+', '', it[1]))); first = True
        elif k == 'p':
            if it[1].startswith('The simulation code, data files'): continue
            P('Paragraph' if first else 'New paragraph', it[1]); first = False
        elif k == 'bul':
            P('Bulleted list', it[1])
        elif k == 'eq':
            q = d.add_paragraph(style=SM['Displayed equation']); q.add_run('\t'); add_marked(q, it[1]); q.add_run('\t(%s)' % it[2])
        elif k == 'fig':
            fig_n += 1; q = d.add_paragraph(style=SM['Normal']); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; q.add_run().add_picture(os.path.join(HERE, 'figures', it[1]), width=Inches(min(4.6, it[2] * 1.4)))
            P('Figure caption', '%s. %s' % (it[3], it[4]), bold_lead='Figure %d. ' % fig_n)
        elif k == 'tab':
            tab_n += 1; P('Table title', it[1], bold_lead='Table %d. ' % tab_n)
            heads, rows, widths = it[2], it[3], it[4]; tb = d.add_table(rows=1, cols=len(heads)); tot = float(sum(widths)); tblPr = tb._tbl.tblPr; bd = OxmlElement('w:tblBorders')
            for side in ('top', 'bottom', 'insideH'):
                e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:space'), '0'); e.set(qn('w:color'), 'auto'); bd.append(e)
            tblPr.append(bd)
            for j, h in enumerate(heads): cell = tb.rows[0].cells[j]; cell.text = ''; add_marked(cell.paragraphs[0], h, size=10, bold=True); cell.width = Inches(5.6 * widths[j] / tot)
            for rr in rows:
                cells = tb.add_row().cells
                for j, v in enumerate(rr): cells[j].text = ''; add_marked(cells[j].paragraphs[0], v, size=10); cells[j].width = Inches(5.6 * widths[j] / tot)
            d.add_paragraph(style=SM['Normal']); first = False
    P('Heading 1', 'Disclosure statement'); P('Paragraph', '[To be completed by the authors: state any potential conflict of interest, or that there is none.]')
    P('Heading 1', 'Funding'); P('Paragraph', '[To be completed by the authors.]')
    P('Heading 1', 'Data availability statement'); P('Paragraph', 'The simulation code, data files, and result tables are openly available at https://github.com/thanwin19/agrovoltaic-canopy-srmc. The weather data are public (NASA POWER, PVGIS).')
    P('Heading 1', 'References')
    for i, ref in enumerate(T.REFS, 1): P('References', '[%d] %s' % (i, ref))
    d.core_properties.title = T.TITLE; d.core_properties.author = ''; d.core_properties.last_modified_by = ''
    d.save(out); return out
if __name__ == '__main__':
    print(build(os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', 'Taylor_and_Francis', 'International_Journal_of_Green_Energy', 'SRMC_Manuscript_International_Journal_of_Green_Energy.docx'))))
