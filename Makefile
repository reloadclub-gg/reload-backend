# Service
up:
	docker-compose up -d --scale django=3 --scale celery=3
	sh ./pipenv-run migrate
	sh ./pipenv-run loaddata

chown:
	sudo chown -R ${USER}:${USER} .

startapp:
	sh ./pipenv-run manage startapp $(params)
	make chown

down:
	docker-compose down -v

halt:
	docker-compose down

logs:
	docker-compose logs -f $(params)

reset:
	make down
	docker-compose up -d --build --scale django=3 --scale celery=3
	sh ./pipenv-run migrate
	sh ./pipenv-run loaddata

refresh:
	make halt
	docker-compose up -d --scale django=3 --scale celery=3

pipinstall:
	docker-compose run --rm django pipenv install $(params)
	make reset

pipremove:
	docker-compose run --rm django pipenv uninstall $(params)
	make reset
