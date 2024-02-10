objects = entrecote.py ferris.py main.py roxy.py wsgi.py

.PHONY: clean full-install install server wsgi wsgi-config wsgi-server

.entrecote:
	mkdir -p .entrecote

.venv:
	python3 -m venv .venv

install: .entrecote .venv requirements.txt
	.venv/bin/pip install `grep --invert-match mod-wsgi-standalone requirements.txt`

server: .venv/bin/python3 $(objects)
	.venv/bin/python3 main.py

wsgi: install requirements.txt
	.venv/bin/pip install `grep mod-wsgi-standalone requirements.txt`

wsgi-server: .venv/bin/mod_wsgi-express $(objects)
	.venv/bin/mod_wsgi-express start-server wsgi.py

wsgi-config: .venv/bin/mod_wsgi-express
	.venv/bin/mod_wsgi-express module-config

clean: requirements.txt
	.venv/bin/pip uninstall --requirement requirements.txt \
  rm -r .venv \
  rm -r .entrecote
