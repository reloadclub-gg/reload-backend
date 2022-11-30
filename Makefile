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

reset-migrations:
	make down
	find . -name '00*_*.py' -delete
	docker-compose up -d
	sh ./pipenv-run makemigrations
	sh ./pipenv-run migrate
	sh ./pipenv-run loaddata

pipinstall:
	docker-compose run --rm django pipenv install $(params)
	make reset
