# -*- coding: utf-8 -*-
"""Fills the OFFICIAL MDPI Word templates (energies-template.dot and agronomy-template.dot, downloaded from mdpi-res.com, the links on each journal's Instructions for Authors page)
with the project paper, using the templates' own MDPI_* styles.   python build_mdpi_official.py"""
import os, re
os.environ['PROJECT'] = '1'
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import paper_text as T
from build_publisher_versions import add_marked, AUTHORS, KEYWORDS
HERE = os.path.dirname(os.path.abspath(__file__)); TD = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', '_official_templates'))
ABBR = [('PAR', 'photosynthetically active radiation'), ('GHI', 'global horizontal irradiance'), ('VPD', 'vapor pressure deficit'), ('PVGIS', 'Photovoltaic Geographical Information System'), ('NASA POWER', 'NASA Prediction of Worldwide Energy Resources'), ('INR', 'Indian rupee')]

def clear(p):
    for r in list(p._p):
        if r.tag != qn('w:pPr'): p._p.remove(r)
def build(journal_key, out):
    d = Document(os.path.join(TD, 'MDPI_%s_template.docx' % journal_key)); body = d.element.body; kids = list(body)
    P0 = d.paragraphs; cut = next(i for i, p in enumerate(P0) if p.style.name == 'MDPI_2.1_heading1')          # first heading = "0. How to Use This Template"
    first = P0[cut]._p
    for k in kids[kids.index(first):-1]: body.remove(k)
    P = d.paragraphs
    def setp(p, runs):
        clear(p)
        for t, b, sup in runs: r = p.add_run(t); r.bold = b or None; r.font.superscript = sup or None
    setp(P[0], [('Article', False, False)]); setp(P[1], [(T.TITLE, False, False)])
    runs = []; n = len(AUTHORS)
    for i, a in enumerate(AUTHORS):
        runs.append((a + ' ', False, False)); runs.append(('1' + (',*' if i == 0 else ''), False, True)); runs.append((', ' if i < n - 2 else (' and ' if i == n - 2 else ''), False, False))
    setp(P[2], runs)
    setp(P[3], [('1\tDepartment of Electrical and Electronics Engineering, Thiagarajar College of Engineering, Madurai 625 015, India; [e-mail addresses of the authors]', False, False)])
    P[4]._p.getparent().remove(P[4]._p); P = d.paragraphs
    setp(P[4], [('*\tCorrespondence: [corresponding author e-mail]', False, False)])
    ab = T.ABSTRACT.replace('Abstract - ', '', 1)
    setp(P[5], [('Abstract: ', True, False), (ab, False, False)])
    setp(P[6], [('Keywords: ', True, False), ('; '.join(KEYWORDS), False, False)])
    SM = {s.name: s for s in d.styles}
    def para(style, text, bold_lead=None):
        q = d.add_paragraph(style=SM[style])
        if bold_lead: q.add_run(bold_lead).bold = True
        add_marked(q, text); return q
    h1 = h2 = fig_n = tab_n = 0; after_eq = False
    for it in T.BODY:
        k = it[0]
        if k == 'h1':
            if it[1] == 'Data Availability': continue
            h1 += 1; h2 = 0; para('MDPI_2.1_heading1', '%d. %s' % (h1, it[1]))
        elif k == 'h2':
            h2 += 1; para('MDPI_2.2_heading2', '%d.%d. %s' % (h1, h2, re.sub(r'^[IVX]+\.\s+', '', it[1])))
        elif k == 'p':
            if it[1].startswith('The simulation code, data files'): continue
            para('MDPI_3.2_text_no_indent' if after_eq else 'MDPI_3.1_text', it[1]); after_eq = False
        elif k == 'bul':
            para('MDPI_3.8_bullet', it[1])
        elif k == 'eq':
            q = d.add_paragraph(style=SM['MDPI_3.9_equation']); q.add_run('\t'); add_marked(q, it[1]); q.add_run('\t(%s)' % it[2]); after_eq = True
        elif k == 'fig':
            fig_n += 1; q = d.add_paragraph(style=SM['MDPI_5.2_figure']); q.add_run().add_picture(os.path.join(HERE, 'figures', it[1]), width=Inches(min(4.2, it[2] * 1.3)))
            c = d.add_paragraph(style=SM['MDPI_5.1_figure_caption']); c.add_run('Figure %d. ' % fig_n).bold = True; add_marked(c, '%s. %s' % (it[3], it[4]))
        elif k == 'tab':
            tab_n += 1; c = d.add_paragraph(style=SM['MDPI_4.1_table_caption']); c.add_run('Table %d. ' % tab_n).bold = True; add_marked(c, it[1])
            heads, rows, widths = it[2], it[3], it[4]; tb = d.add_table(rows=1, cols=len(heads)); tot = float(sum(widths)); tblPr = tb._tbl.tblPr; bd = OxmlElement('w:tblBorders')
            for side in ('top', 'bottom', 'insideH'):
                e = OxmlElement('w:' + side); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:space'), '0'); e.set(qn('w:color'), 'auto'); bd.append(e)
            tblPr.append(bd)
            for j, h in enumerate(heads):
                cell = tb.rows[0].cells[j]; cell.text = ''; cell.paragraphs[0].style = SM['MDPI_4.2_table_body']; add_marked(cell.paragraphs[0], h, bold=True); cell.width = Inches(5.4 * widths[j] / tot)
            for rr in rows:
                cells = tb.add_row().cells
                for j, v in enumerate(rr): cells[j].text = ''; cells[j].paragraphs[0].style = SM['MDPI_4.2_table_body']; add_marked(cells[j].paragraphs[0], v); cells[j].width = Inches(5.4 * widths[j] / tot)
            d.add_paragraph(style=SM['MDPI_3.1_text'])
    for lead, txt in (('Author Contributions: ', '[to be completed by the authors, for example: Conceptualization, ...; methodology, ...; software, ...; writing, ...].'), ('Funding: ', '[to be completed by the authors; for example "This research received no external funding"].'),
                      ('Institutional Review Board Statement: ', 'Not applicable.'), ('Informed Consent Statement: ', 'Not applicable.'),
                      ('Data Availability Statement: ', 'The simulation code, data files, and result tables are available at https://github.com/thanwin19/agrovoltaic-canopy-srmc. The weather data are public (NASA POWER, PVGIS).'),
                      ('Acknowledgments: ', '[optional].'), ('Conflicts of Interest: ', '[to be completed by the authors].')):
        para('MDPI_6.2_back_matter', txt, bold_lead=lead)
    para('MDPI_2.1_heading1', 'Abbreviations'); para('MDPI_3.2_text_no_indent', 'The following abbreviations are used in this manuscript:')
    for a, b in ABBR: para('MDPI_3.2_text_no_indent', b, bold_lead=a + '\t')
    para('MDPI_2.1_heading1', 'References')
    for i, ref in enumerate(T.REFS, 1): para('MDPI_8.1_references', '%d. %s' % (i, ref))
    d.core_properties.title = T.TITLE; d.core_properties.author = ''; d.core_properties.last_modified_by = ''
    d.save(out); return out
if __name__ == '__main__':
    base = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper', 'MDPI'))
    print(build('energies', os.path.join(base, 'Energies', 'SRMC_Manuscript_Energies.docx'))); print(build('agronomy', os.path.join(base, 'Agronomy', 'SRMC_Manuscript_Agronomy.docx')))
