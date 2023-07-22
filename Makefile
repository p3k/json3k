install: requirements.txt
	python3 -m venv .venv
	. .venv/bin/activate
	.venv/bin/pip install -r requirements.txt
	sudo mkdir -p /var/lib/entrecote

server: main.py roxy.py ferris.py wsgi.py
	.venv/bin/python3 main.py

wsgi: main.py roxy.py ferris.py wsgi.py
	.venv/bin/mod_wsgi-express start-server wsgi.py

config:
	.venv/bin/mod_wsgi-express module-config
