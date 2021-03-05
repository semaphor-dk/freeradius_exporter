.PHONY: clean

clean:
	rm -rf dist/ build/ freeradius_exporter.egg-info/

install:
	python3 setup.py install

dist: freeradius_exporter/freeradius_exporter.py setup.py Makefile freeradius_exporter/dictionary.freeradius.pyrad
	python3 setup.py sdist
