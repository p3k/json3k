objects = entrecote.py ferris.py main.py roxy.py wsgi.py

.PHONY: apache-config clean full-install install server wsgi wsgi-server

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

# Everything needed in a real Apache config for this checkout – process
# group name and paths match the rest of this file’s own examples.
# wsgi/wsgi-server run their own bundled, private Apache instead,
# unrelated to whatever Apache/Python is actually installed on the
# system, and never a source for this (ABI mismatch risk). Prints
# nothing at all if the module isn’t installed yet, rather than a
# confusing mix of an error and a config that’s still missing its
# first line. Debian/Ubuntu-specific, matching the package name it
# queries.
apache-config:
	@so=$$(dpkg -L libapache2-mod-wsgi-py3 2>/dev/null | grep '\.so$$'); \
	if [ -z "$$so" ]; then \
	  echo "libapache2-mod-wsgi-py3 is not installed – run: sudo apt install libapache2-mod-wsgi-py3" >&2; \
	  exit 1; \
	fi; \
	dir=$$(pwd); \
	echo "LoadModule wsgi_module $$so"; \
	echo "WSGIRestrictEmbedded On"; \
	echo "WSGISocketPrefix /var/run/apache2/wsgi"; \
	echo; \
	printf 'WSGIDaemonProcess json3k \\\n  python-home=%s/.venv \\\n  home=%s \\\n  processes=4 \\\n  threads=15\n' "$$dir" "$$dir"; \
	echo; \
	echo "WSGIScriptAlias /json3k $$dir/wsgi.py process-group=json3k"; \
	echo; \
	echo "<Location /json3k>"; \
	echo "   WSGIApplicationGroup %{GLOBAL}"; \
	echo "   Require all granted"; \
	echo "</Location>"

clean: requirements.txt
	.venv/bin/pip uninstall --requirement requirements.txt \
  rm -r .venv \
  rm -r .entrecote
