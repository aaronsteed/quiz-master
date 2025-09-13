VERSION := $(shell grep '^version =' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
TARBALL := dist/quiz-master.tar.gz
SHA256 := $(shell shasum -a 256 $(TARBALL) | awk '{print $$1}')
FORMULA := brew/Formula/quiz-master.rb

build-exec:
	pyinstaller --onefile main.py --name quiz-master --add-data "data/chart-starter:data/chart-starter"

package: build-exec
	@mkdir -p dist
	@tar -czvf $(TARBALL) dist/quiz-master

update-formula: package
	@sed -i '' "s|url \".*\"|url br\"$(TARBALL)\"|" $(FORMULA)
	@sed -i '' "s|sha256 \".*\"|sha256 \"$(SHA256)\"|" $(FORMULA)
	@sed -i '' "s|version \".*\"|version \"$(VERSION)\"|" $(FORMULA)

brew-install: update-formula
	@brew install --formula ./$(FORMULA) --force --tap=aaronsteed/quiz-master
