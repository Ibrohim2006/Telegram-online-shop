.PHONY: build up down migrate shell bot

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	docker-compose exec web python manage.py makemigrations
	docker-compose exec web python manage.py migrate

shell:
	docker-compose exec web python manage.py shell

bot:
	docker-compose exec bot python manage.py run_aiogram_bot

superuser:
	docker-compose exec web python manage.py createsuperuser

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -f
