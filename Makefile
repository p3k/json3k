objects = main.py roxy.py ferris.py wsgi.py

.PHONY: install server wsgi config clean

install: requirements.txt
	python3 -m venv .venv
	. .venv/bin/activate
	.venv/bin/pip install --requirement requirements.txt
	mkdir -p .entrecote

server: .venv/bin/python3 $(objects)
	.venv/bin/python3 main.py

wsgi: .venv/bin/mod_wsgi-express $(objects)
	.venv/bin/mod_wsgi-express start-server wsgi.py

config: .venv/bin/mod_wsgi-express
	.venv/bin/mod_wsgi-express module-config

clean: requirements.txt
	.venv/bin/pip uninstall --requirement requirements.txt
