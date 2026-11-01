# -*- coding: utf-8 -*-
"""One manuscript file per target journal (project paper: Reviews 0-5, month run with real weather, prototype photo) + a cover-letter draft each,
written to  srmc-twin/reseach paper/<Publisher>/<Journal>/ , and the common paper to  srmc-twin/reseach paper/common/.   python build_journal_versions.py"""
import os, shutil, subprocess
os.environ['PROJECT'] = '1'
import build_publisher_versions as B
import paper_text as T
from docx import Document
from docx.shared import Pt, Cm
HERE = B.HERE; DEST = os.path.abspath(os.path.join(HERE, '..', 'srmc-twin', 'reseach paper'))
SOFFICE = r'C:\Program Files\LibreOffice\program\soffice.exe'
J = [
 ('IEEE', 'IEEE', 'IEEE Access', 'IEEE_Access', 'Multidisciplinary open-access engineering journal that publishes simulation-based engineering studies; the controller, the simulation and the implementation sections fit it.', 'Reviewers usually ask for reproducible code and a comparison with existing control methods: the code and data are on GitHub and the paper compares against fixed, tracking and monthly-plan designs.'),
 ('Elsevier', 'Elsevier', 'Solar Energy', 'Solar_Energy', 'Solar-specific journal: tilt control, shading and energy yield are within its scope.', 'Reviewers are likely to ask for measured irradiance or field data; the paper checks the sunlight model against NASA POWER and PVGIS but has no measurement at the site.'),
 ('Elsevier', 'Elsevier', 'Computers and Electronics in Agriculture', 'Computers_and_Electronics_in_Agriculture', 'Sensing, control and decision support in agriculture: a six-sensor controller with irrigation and crop light fits the scope.', 'Reviewers are likely to ask for crop experiments; the paper states that the crop model is not validated against field data and gives a measurement protocol.'),
 ('MDPI', 'MDPI', 'Energies', 'Energies', 'Broad energy journal that accepts simulation studies of agrivoltaic systems and control.', 'Fee-based open access; check the article processing charge and any waiver before submitting.'),
 ('MDPI', 'MDPI', 'Agronomy', 'Agronomy', 'Crop-focused journal that publishes agrivoltaic work; the crop light and water parts fit.', 'A crop journal will weigh crop data heavily; this is the weakest scope fit because the crop model is not validated in the field.'),
 ('Springer Nature', 'Springer Nature', 'Energy, Sustainability and Society', 'Energy_Sustainability_and_Society', 'Energy, land use and society: the farmer-income and land-sharing angle fits.', 'Reviewers may ask for a stronger economic and social analysis; the paper says the investor case is weak at the assumed prices.'),
 ('Taylor and Francis', 'Taylor and Francis', 'International Journal of Green Energy', 'International_Journal_of_Green_Energy', 'Green and renewable energy systems, including solar and control.', 'May require author-year references; convert the numbered references to the journal style.'),
]
def letter(journal, fit, risk, path):
    d = Document(); d.styles['Normal'].font.name = 'Times New Roman'; d.styles['Normal'].font.size = Pt(11)
    for s in d.sections: s.left_margin = s.right_margin = Cm(2.5)
    P = lambda t, b=False: d.add_paragraph().add_run(t).__setattr__('bold', b)
    d.add_paragraph('[Date]'); d.add_paragraph('The Editor-in-Chief\n%s' % journal); d.add_paragraph('Dear Editor,')
    d.add_paragraph('We submit the manuscript "%s" for consideration as a research article in %s.' % (T.TITLE, journal))
    d.add_paragraph('Agrovoltaic systems share land between crops and solar panels, but a fixed panel angle favours either the crop or the electricity. We define a co-optimization accuracy that scores a tilt strategy against the best possible angle for the same objective, and we present a six-sensor tilt controller that reaches 99.6 to 99.7 percent of that best score at seven climates in simulation, against 89.1 to 91.5 percent for a fixed 45 degree tilt. The paper also reports a simulated month driven by real NASA POWER weather and describes a wire-driven canopy and a scaled prototype.')
    d.add_paragraph('Why this journal (our judgement, please check the journal\'s aims and scope): %s' % fit)
    d.add_paragraph('What we state openly: all results are simulation and the sensors are software models of named commercial devices; the accuracy is measured against the controller\'s own objective, not against crop yield; no field measurement is reported. %s' % risk)
    d.add_paragraph('[Authors to confirm before sending: the work is original, has not been published and is not under consideration elsewhere; all authors have approved the manuscript; there is no conflict of interest, or state it.]')
    d.add_paragraph('Code, data and results are available at https://github.com/thanwin19/agrovoltaic-canopy-srmc.')
    d.add_paragraph('Suggested reviewers: [to be completed by the authors].'); d.add_paragraph('Sincerely,\n[corresponding author name, affiliation, e-mail]\nThanwin S S, Chandru P M, Kuberaeshwaran S, Mukilan A, and M. Meenakshi Devi\nThiagarajar College of Engineering, Madurai, India')
    d.save(path)
os.makedirs(DEST, exist_ok=True)
# IEEE-style two-column file from the ProComm build
subprocess.run(['python', os.path.join(HERE, 'build_paper.py')], env=dict(os.environ, PROJECT='1'), check=True, cwd=HERE)
made = []
for pub, cfgname, journal, folder, fit, risk in J:
    outdir = os.path.join(DEST, pub.replace(' ', '_'), folder); os.makedirs(outdir, exist_ok=True)
    fname = 'SRMC_Manuscript_%s.docx' % folder
    if pub == 'IEEE': shutil.copy(os.path.join(HERE, 'SRMC_FinalYear_Project_Paper.docx'), os.path.join(outdir, fname))
    else: B.build(cfgname, B.PUBS[cfgname], journal=journal, outdir=outdir, filename=fname)
    letter(journal, fit, risk, os.path.join(outdir, 'Cover_letter_DRAFT_%s.docx' % folder)); made.append((pub, journal, outdir))
for pub, journal, outdir in made:
    subprocess.run([SOFFICE, '--headless', '--convert-to', 'pdf', '--outdir', outdir] + [os.path.join(outdir, f) for f in os.listdir(outdir) if f.endswith('.docx')], capture_output=True)
# the common paper
cdir = os.path.join(DEST, 'common'); os.makedirs(cdir, exist_ok=True)
env = dict(os.environ); env.pop('PROJECT', None)
subprocess.run(['python', os.path.join(HERE, 'build_paper.py')], env=env, check=True, cwd=HERE); subprocess.run(['python', os.path.join(HERE, 'build_paper.py')], env=dict(env, CAMERA='1'), check=True, cwd=HERE)
for f in ('SRMC_Research_Paper.docx', 'SRMC_Research_Paper_CAMERA_READY_SAMPLE.docx'): shutil.copy(os.path.join(HERE, f), os.path.join(cdir, f))
subprocess.run([SOFFICE, '--headless', '--convert-to', 'pdf', '--outdir', cdir] + [os.path.join(cdir, f) for f in os.listdir(cdir) if f.endswith('.docx')], capture_output=True)
shutil.copy(os.path.join(HERE, 'PRIOR_ART_SEARCH.md'), os.path.join(cdir, 'PRIOR_ART_SEARCH.md'))
print('done', DEST)
