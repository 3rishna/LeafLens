LeafLens — Overleaf submission package
======================================

HOW TO USE
----------
1. Go to Overleaf -> New Project -> Upload Project -> select this .zip
2. Overleaf should pick main.tex as the root document automatically.
   If not: Menu -> Main document -> main.tex
3. Compiler: pdfLaTeX (Overleaf's default; the class is configured for it via the
   [pdflatex] documentclass option). Menu -> Compiler -> pdfLaTeX if needed.
4. Recompile. You should get a 21-page document with no errors.

CONTENTS
--------
  main.tex        the manuscript (Springer Nature sn-jnl class)
  sn-jnl.cls      the Springer Nature journal class  -- see note below
  figures/        the 9 figures referenced by main.tex
  README.txt      this file

ABOUT sn-jnl.cls
----------------
sn-jnl.cls is not distributed via CTAN, so Overleaf will not supply it automatically
and it must travel with the project. The copy included here is v0.1 (2019/11/18),
redistributed under the LaTeX Project Public License v1.3c as stated in its header.

It builds this document cleanly, but it is NOT the current release. Springer's current
template is v3.1 (Dec 2024). Before submitting, consider replacing this file with the
official copy, which you can get by either:
  - opening the "Springer Nature LaTeX Template" in the Overleaf template gallery, or
  - downloading the template from Springer's LaTeX author-support pages, then checking
    the specific submission guidelines for your target journal.
Simply overwrite sn-jnl.cls in the project; nothing in main.tex should need to change.

THREE THINGS main.tex ALREADY HANDLES
-------------------------------------
These are applied in the preamble; do not remove them or the build will break:

1. \usepackage{manyfoot}
   sn-jnl calls \SetFootnoteHook and \DeclareNewFootnote inside an \AtBeginDocument
   hook but does not itself load the package that defines them.

2. Comma-separated \keywords
   \and is llncs syntax. Inside sn-jnl it collides with the author-block tabular and
   produces "Misplaced \crcr" during \maketitle.

3. Document class option sn-mathphys-num
   The default sn-basic puts natbib in author-year mode, which is incompatible with the
   manual numeric \thebibliography this manuscript uses. sn-nature also works. Change
   this to whichever numbered reference style your target journal specifies.

BIBLIOGRAPHY
------------
References are a manual \thebibliography list inside main.tex, so there is no .bib file
and no BibTeX pass is required. If your journal requires BibTeX with one of Springer's
.bst files, convert the list and add the .bst from the official template.
