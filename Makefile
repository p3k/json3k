DATASTORE_EMULATOR_HOST=localhost:8081
DATASTORE_PROJECT_ID=p3k-services

INDEX_FILE=~/.config/gcloud/emulators/datastore/WEB-INF/index.yaml

server: main.py
	DATASTORE_EMULATOR_HOST=$(DATASTORE_EMULATOR_HOST) \
	DATASTORE_PROJECT_ID=$(DATASTORE_PROJECT_ID) \
	python main.py

datastore:
	DATASTORE_EMULATOR_HOST=$(DATASTORE_EMULATOR_HOST) \
	DATASTORE_PROJECT_ID=$(DATASTORE_PROJECT_ID) \
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
