etl:
	poetry install && poetry run python ./infra_cassandra/etl.py

setup:
	docker network create cassandra_network

up:
	docker compose up --build -d

jup:
	docker exec -it jupyter jupyter server list | grep token

cas:
	docker exec -it cassandra1 /bin/bash

down:
	docker compose down
