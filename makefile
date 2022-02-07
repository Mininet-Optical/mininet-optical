MODULE = mnoptical
SRCS = $(MODULE)/*.py $(MODULE)/*/*.py
PKG = pyproject.toml setup.cfg setup.py

# Build python package (wheel/.whl file)
# using pyproject-build (from python 'build' package)
dist wheel: $(SRCS) $(PKG) makefile
	pyproject-build --wheel

# Install python package
install: dist
	sudo pip3 uninstall mininet-optical
	sudo pip3 install dist/mininet_optical*.whl

# Development/editable installation
develop: $(SRCS) $(PKG)
	sudo pip3 uninstall mininet-optical
	sudo pip3 install --editable .

# Install dependencies
# In addition to our package dependencies, we install
# build (for building) and pygraphviz (for examples/)
depend: requirements.txt
	python3 -m pip install -r requirements.txt
	sudo python3 -m pip install -r requirements.txt
	python3 -m pip install build
	sudo apt install python3-pygraphviz

# Run simulator tests
simtest:
	tests/RunTests.sh

# Run emulation tests
emutest:
	sudo examples/runtests.sh

# Run all tests
test: simtest emutest

# Clean up non-source files
clean:
	rm -rf build dist __pycache__ *.egg-info dist
	find . -name -o -name '*.pyc' \
	-o -name '*~' -o -name '#*' -o -name '*.png' \
	| xargs rm -rf
