all:

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
	find . -name __pycache__ -o -name '*.pyc' \
	-o -name '*~' -o -name '#*' -o -name '*.png' \
	| xargs rm -rf
