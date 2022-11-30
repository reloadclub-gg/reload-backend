# GTA Backend
GTA's Python/Django API  

A project built with the following languages and libs to design and expose the API for the GTA application.  
[python 3.8](https://docs.python.org/3.8/)  
[django](https://www.djangoproject.com/)  
[django-ninja](https://django-ninja.rest-framework.com/)  
[postgresql](https://www.postgresql.org/docs/current/)  
[redis](https://redis.io/)  
[django-channels](https://channels.readthedocs.io/en/stable/)  
[celery](https://docs.celeryproject.org/en/stable/)

# Requirements
[git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git),
[docker](https://docs.docker.com/install/), and
[docker-compose](https://docs.docker.com/compose/install/).

# Setup
1. Clone the project:
```bash
git clone https://github.com/3c-gg/gta-backend.git
cd gta-backend
```
2. Duplicate `.template.env` to `.env` and make sure you have all envvars set.
3. Run `make up` to get the project up and running.

# Helper scripts
`./pipenv-run` is a helper command that wraps `docker-compose` to expose python-env-aware commands in a
container. You can use it to run `pipenv install` or `./manage.py`. See the Pipfile `[scripts]` section for additional commands.  

On the `Makefile` there are some helper entrypoints that wrap the other wrappers.  

# Other instructions
- `make up` is a helper command that brings up the stack in docker compose, migrate db and load some starter data from from fixtures.  
- `./pipenv-run test` to run tests.  
- `./pipenv-run lint` to check if the code comply with the project's code rules.  
- Access the api on `http://localhost:8000` and the websocket on `ws://localhost:8000`.  
- Admin credentials are `admin@gta.com.br` / `adminadmin`.  
- If you're having permission issues, run `make chown`. That should set your user as the owner of project files.  
- To add any new packages, run `make pipinstall params={PACKAGE_NAME}`. This will install the new package and restart the compose services.
