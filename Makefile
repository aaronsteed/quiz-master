build-exec:
	pyinstaller --onefile main.py --name quiz-master --add-data "quiz_master/chart-starter:quiz_master/chart-starter"