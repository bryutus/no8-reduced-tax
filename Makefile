SUMMARIZE_FILE=

run:
	python3 -m summarize.main resources/$(SUMMARIZE_FILE) $(SUMMARIZE_MONTH)

test:
	python3 -m unittest discover -v
