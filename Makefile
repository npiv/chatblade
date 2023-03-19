venv/bin/activate: requirements.txt
	python3 -m venv venv 
	./venv/bin/pip install -r requirements.txt

setup: venv/bin/activate

clean: clean-build clean-pyc

sanitize: clean clean-venv

clean-venv:
	rm -rf venv/

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
