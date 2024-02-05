export TEXINPUTS=.:latex/:
LATEX=pdflatex
FLAGS=-halt-on-error -shell-escape
BUILD_FOLDER=build/
PDF_NAME=vnoi-magazine-2024.pdf
OUTPUT=$(BUILD_FOLDER)/$(PDF_NAME)

all: magazine

install-texlive-ubuntu:
	sudo apt update
	sudo apt install \
		ghostscript \
		texlive \
		texlive-fonts-recommended \
		texlive-latex-extra \
		texlive-lang-other \
		texlive-plain-generic

clean:
	rm src/*.log
	rm src/*.out
	rm src/*.toc
	rm src/*.aux

$(BUILD_FOLDER):
	mkdir -p $(BUILD_FOLDER)
	
magazine: render-articles | $(BUILD_FOLDER)
	make render-pdf
	
render-articles:
	export PYTHONPATH="${PYTHONPATH}:./scripts/"; \
	mkdir -p src/articles; \
	for article in ./articles/*.md ./interviews/*.md; do \
		echo Processing $$article; \
		marko -e marko_latex_extension -o src/$${article//.md/.latex} $$article; \
	done

render-pdf: $(BUILD_FOLDER)
	cd src; \
	$(LATEX) $(FLAGS) magazine.latex; \
	cd ..; \
	cp src/magazine.pdf $(OUTPUT)
