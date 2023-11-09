# Service
up:
	docker-compose up -d
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
	docker-compose up -d --build
	sh ./pipenv-run migrate
	sh ./pipenv-run loaddata

refresh:
	make halt
	docker-compose up -d

pipinstall:
	docker-compose run --rm api pipenv install $(params)
	make reset

pipremove:
	docker-compose run --rm api pipenv uninstall $(params)
	make reset

resetlocust:
	docker-compose down -v
	docker-compose up -d
	sh ./pipenv-run migrate
	sh ./pipenv-run createsuperuser
