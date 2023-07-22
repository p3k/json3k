install: requirements.txt
	python3 -m venv .venv
	. .venv/bin/activate
	.venv/bin/pip install --requirement requirements.txt
	sudo mkdir -p /var/lib/entrecote

server: .venv/bin/python3 main.py roxy.py ferris.py wsgi.py
	.venv/bin/python3 main.py

wsgi: .venv/bin/mod_wsgi-express main.py roxy.py ferris.py wsgi.py
	.venv/bin/mod_wsgi-express start-server wsgi.py

config: .venv/bin/mod_wsgi-express
	.venv/bin/mod_wsgi-express module-config

clean: requirements.txt
	.venv/bin/pip uninstall --requirement requirements.txt
