# VNOI magazine 2024

TODO read online link.

## Requisite 

### Python

This repository requires Python3.

To install the required packages, run the following command:

```sh
# make a virtual environment
python3 -m virtualenv venv

# activate the virtual environment
source venv/bin/activate

# install the required packages
pip install -r requirements.txt
```

### $\LaTeX$

- Texlive (for `pdflatex` and packages used in this repo).
- TODO list latex packages

### Makefile

- Makefile
  
## Building
```sh
make
```

Note that in order to render the TOC, `make` command need to be ran twice. The
first time $\LaTeX$ will render will dump the TOC and the second time it will
render the TOC.

## Generate latex source from markdown
```sh
make render-articles
```
With this command, all the markdown files in `./articles` and `./interviews`
will be transformed into the corresponding latex files in `./src/articles` and
`./src/interviews` respectively.
