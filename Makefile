objects = entrecote.py ferris.py main.py roxy.py wsgi.py

.PHONY: apache-config apache-wsgi-config clean full-install install server wsgi wsgi-server

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

# For a real Apache deployment. wsgi/wsgi-server run their own bundled,
# private Apache instead – unrelated to whatever Apache/Python is
# actually installed on the system, and never a source for a real
# Apache config (ABI mismatch risk). Debian/Ubuntu-specific, matching
# the package name this reads.
apache-wsgi-config:
	@so=$$(dpkg -L libapache2-mod-wsgi-py3 2>/dev/null | grep '\.so$$'); \
	if [ -z "$$so" ]; then \
	  echo "libapache2-mod-wsgi-py3 is not installed – run: sudo apt install libapache2-mod-wsgi-py3" >&2; \
	  exit 1; \
	fi; \
	echo "LoadModule wsgi_module $$so"

# Everything actually needed in a real Apache config for this checkout,
# not just the module line – process-group name and paths match the
# rest of this file’s own examples. Prints the rest even if
# apache-wsgi-config’s LoadModule line fails (e.g. package not
# installed yet), since that alone doesn’t block the rest from being
# useful.
apache-config:
	-@$(MAKE) --no-print-directory apache-wsgi-config
	@echo "WSGIRestrictEmbedded On"
	@echo "WSGISocketPrefix /var/run/apache2/wsgi"
	@echo
	@dir=$$(pwd); \
	printf 'WSGIDaemonProcess json3k \\\n  python-home=%s/.venv \\\n  home=%s \\\n  processes=4 \\\n  threads=15\n' "$$dir" "$$dir"
	@echo
	@dir=$$(pwd); echo "WSGIScriptAlias /json3k $$dir/wsgi.py process-group=json3k"
	@echo
	@echo "<Location /json3k>"
	@echo "   WSGIApplicationGroup %{GLOBAL}"
	@echo "   Require all granted"
	@echo "</Location>"

clean: requirements.txt
	.venv/bin/pip uninstall --requirement requirements.txt \
  rm -r .venv \
  rm -r .entrecote
