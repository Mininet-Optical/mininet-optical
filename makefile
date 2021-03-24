all:

depend: requirements.txt
	python3 -m pip install -r requirements.txt
	sudo python3 -m pip install -r requirements.txt

clean:
	find . -name __pycache__ -o -name '*.pyc' \
	-o -name '*~' -o -name '#*' | xargs rm -rf
