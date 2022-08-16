MODULE = mnoptical
SRCS = $(MODULE)/*.py $(MODULE)/*/*.py
PKG = pyproject.toml setup.cfg setup.py
PIP = python3 -m pip
APT = apt -y

# Build python package (wheel/.whl file)
# using pyproject-build (from python 'build' package)
dist wheel: $(SRCS) $(PKG) makefile clean
	pyproject-build --wheel

# Install python package
install: dist
	$(PIP) install --upgrade --verbose dist/*.whl
	sudo $(PIP) install --upgrade --verbose dist/*.whl

# Development/editable installation
# FIXME: This doesn't seem to work properly
develop: $(SRCS) $(PKG)
	sudo $(PIP) uninstall mininet-optical
	sudo $(PIP) install --editable .

# Install dependencies
# In addition to our package dependencies, we install
# build and wheel (for building) and pygraphviz (for examples/)
depend: requirements.txt
	sudo $(PIP) install -r requirements.txt
	sudo $(PIP) install build wheel
	sudo $(APT) install python3-pygraphviz

# Run simulator tests
simtest:
	tests/RunTests.sh

# Run emulation tests
emutest: certs
	examples/runtests.sh

# Run demo test
demotest:
	sudo python3 -m mnoptical.ofcdemo.demo_2021 test

# Run cross validation sanity check
crossvalsanity:
	(cd cross-validation-tests && bash -x ./cross_validation.sh)

# Run all tests
test: simtest emutest demotest crossvalsanity

# Generate fake certs for netconf client/server
certs: makecerts.sh
	./makecerts.sh

# Generate html documentation
doc:
	make -C docs html

docclean:
	rm -rf docs/build/*

# Generate and serve local html documentation
docserve: doc
	python3 -m http.server -d docs/build/html

# Clean up non-source files
fileclean:
	rm -rf build dist *.egg-info
	find . -name '*.pyc' -o -name __pycache__ \
	-o -name '*~' -o -name '#*' -o -name '*.png' \
	| xargs rm -rf
	rm -rf testcerts mnoptical/demo/*txt Monitor_Lightpath.txt


# Clean up everything
clean: fileclean docclean
