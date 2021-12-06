MODULE = mininet_optical
SRCS = $(MODULE)/*.py $(MODULE)/*/*.py
PKG = pyproject.toml setup.cfg setup.py

all:

build: wheel

# Build python package (wheel)
dist wheel: $(SRCS) $(PKG)
	pyproject-build --wheel

# Install python package
install: dist
	sudo pip3 uninstall mininet_optical
	sudo pip3 install dist/mininet_optical*.whl

# Development/editable installation
develop: $(SRCS) $(PKG)
	sudo pip3 uninstall mininet_optical
	sudo pip3 install --editable .

# Install dependencies
depend: requirements.txt
	sudo apt install python3-pygraphviz
	python3 -m pip install -r requirements.txt
	sudo python3 -m pip install -r requirements.txt

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
