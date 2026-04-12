.PHONY: help build up down restart logs ps app-logs db-logs shell-app shell-db reset-db clean

COMPOSE := docker compose

help:
	@printf "Available targets:\n"
	@printf "  make build      Build local containers\n"
	@printf "  make up         Start containers in detached mode\n"
	@printf "  make down       Stop containers\n"
	@printf "  make restart    Restart containers\n"
	@printf "  make logs       Follow all container logs\n"
	@printf "  make ps         Show container status\n"
	@printf "  make app-logs   Follow app logs\n"
	@printf "  make db-logs    Follow database logs\n"
	@printf "  make shell-app  Open a shell in the app container\n"
	@printf "  make shell-db   Open a shell in the database container\n"
	@printf "  make reset-db   Drop and recreate all database tables\n"
	@printf "  make clean      Stop containers and remove volumes\n"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up --build -d

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

app-logs:
	$(COMPOSE) logs -f app

db-logs:
	$(COMPOSE) logs -f db

shell-app:
	$(COMPOSE) exec app sh

shell-db:
	$(COMPOSE) exec db sh

reset-db:
	$(COMPOSE) exec app poetry run flask --app app:create_app reset-db

clean:
	$(COMPOSE) down -v
