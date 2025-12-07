build-exec:
	rm -r dist/
	pyinstaller --onefile main.py --name quiz-master --add-data "quiz_master/chart-starter:quiz_master/chart-starter"
	mv dist/quiz-master ~/.tools