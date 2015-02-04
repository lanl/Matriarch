pandoc=~/.cabal/bin/pandoc
docs=docs/index.md

items=dist/pretty_html dist/guide.pdf dist/guide.docx dist/guide.html dist/guide.txt dist/info.txt

dist.tar.gz: dist $(items)
	 tar czf dist.tar.gz dist/

dist:
	mkdir dist

dist/info.txt:
	echo "User's Guide for Matriarch\nGenerated at `date` by `whoami` on `hostname` via Makefile" > dist/info.txt

dist/pretty_html: dist $(docs)
	mkdocs build
	mv site dist/pretty_html

dist/guide.pdf: dist $(docs) listing-setup.tex
	$(pandoc) -f markdown -t latex --listings -H listing-setup.tex -o dist/guide.pdf < docs/index.md

dist/guide.docx: dist $(doc)
	$(pandoc) -f markdown -t docx -o dist/guide.docx < docs/index.md

dist/guide.html: dist $(doc)
	$(pandoc) -f markdown -t html5 -o dist/guide.html < docs/index.md

dist/guide.txt: dist $(doc)
	$(pandoc) -f markdown -t plain -o dist/guide.txt < docs/index.md

.phony: clean


clean:
	rm -rf dist dist.tar.gz
