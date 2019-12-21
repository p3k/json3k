server : main.py
	python main.py

datastore:
	export DATASTORE_EMULATOR_HOST=localhost:8081; \
	export DATASTORE_PROJECT_ID=p3k-services; \
	gcloud beta emulators datastore start; \
	unset DATASTORE_EMULATOR_HOST; \
	unset DATASTORE_PROJECT_ID; \

upload:
	gcloud app deploy --no-promote

index:
	gcloud datastore indexes create index.yaml

install: requirements.txt
	pip install -r requirements.txt

tasks:
	gcloud app deploy cron.yaml
