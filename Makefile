SUMMARIZE_FILE=

run:
	python3 -m summarize.main resources/$(SUMMARIZE_FILE)

test:
	python3 -m unittest discover -v
