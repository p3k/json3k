install: requirements.txt
	pip install -r requirements.txt

server: main.py roxy.py ferris.py wsgi.py
	python main.py

wsgi: main.py roxy.py ferris.py wsgi.py
	mod_wsgi-express start-server wsgi.py --port 8001

config:
	mod_wsgi-express module-config
