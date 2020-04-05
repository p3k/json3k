INDEX_FILE=~/.config/gcloud/emulators/datastore/WEB-INF/index.yaml

server: main.py
	$(gcloud beta emulators datastore env-init)
	python main.py

datastore:
	$(gcloud beta emulators datastore env-init)
	gcloud beta emulators datastore start

upload:
	gcloud app deploy --no-promote

index:
	gcloud datastore indexes create $(INDEX_FILE)
	cat $(INDEX_FILE) > index.yaml

install: requirements.txt
	pip install -r requirements.txt

tasks:
	gcloud app deploy cron.yaml
