VERSION := $(shell grep '^version =' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
TARBALL := dist/quiz-master.tar.gz
SHA256 := $(shell shasum -a 256 $(TARBALL) | awk '{print $$1}')
FORMULA := brew/Formula/quiz-master.rb

build-exec:
	pyinstaller --onefile main.py --name quiz-master --add-data "data/chart-starter:data/chart-starter"

export:
	mv dist/quiz-master ~/.tools
