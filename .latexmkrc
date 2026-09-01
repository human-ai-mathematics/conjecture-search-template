# latexmk configuration for this project.
# Bibliography is biblatex + biber (single shared fi_references.bib). latexmk runs
# biber automatically from the .bcf control file; we only set sensible defaults so
# that a bare `latexmk` builds the master document into build/ in one shot.
$pdf_mode    = 1;          # build the PDF with pdflatex
$bibtex_use  = 2;          # run the bib backend; use the .bbl even if .bib is absent
$out_dir     = 'build';    # keep all build artifacts under build/

# `latexmk` with no arguments builds the master document.
@default_files = ('main.tex');
