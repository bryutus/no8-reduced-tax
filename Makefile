RESOURCE_FILE=

convert:
	python3 -m convert.main resources/$(RESOURCE_FILE)

run:
	python3 -m summarize.main

test:
	python3 -m unittest discover -v

.PHONY: convert
