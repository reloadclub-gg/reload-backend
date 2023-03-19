# Service
up:
	docker-compose up -d
	sh ./pipenv-run migrate
	sh ./pipenv-run loaddata

chown:
	sudo chown -R ${USER}:${USER} .

startapp:
	docker-compose run --rm django python ./manage.py startapp $(params)
	make chown

down:
	docker-compose down -v

halt:
	docker-compose down

logs:
	docker-compose logs -f $(params)

reset:
	make down
	docker-compose up -d --build
	sh ./pipenv-run migrate
	sh ./pipenv-run loaddata

refresh:
	make halt
	docker-compose up -d

pipinstall:
	docker-compose run --rm django pipenv install $(params)
	make reset

pipremove:
	docker-compose run --rm django pipenv uninstall $(params)
	make reset
