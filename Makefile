install:
	pip install --require-virtualenv --requirement requirements.txt
	sudo mkdir --parent /var/lib/entrecote

server:
	python main.py

wsgi:
	mod_wsgi-express start-server wsgi.py

config:
	mod_wsgi-express module-config

clean:
	pip uninstall --require-virtualenv --requirement requirements.txt
