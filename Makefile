all: help

help:
	@echo " ___ ____ ___  _ ____ ____ ____"
	@echo "  |  |--| |--' | [__] |___ |--|"
	@echo ""
	@echo " setup .................... Install all project dependencies."
	@echo " test ..................... Run all tests."

test:
	@nosetests --with-coverage  --cover-package tapioca tests/

setup:
	@pip install -r requirements.txt
