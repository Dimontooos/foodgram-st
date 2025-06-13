# Foodgram - Платформа для публикации рецептов

## Автор проекта
**Ардеев Дмитрий Юрьевич**  
Студент Северо-Кавказского федерального университета  
Направление: 10.05.03 "Информационная безопасность автоматизированных систем"  
Курс: 3 (очная форма обучения)  

### Контакты
Email: [ardeev.dima2020@yandex.ru](mailto:ardeev.dima2020@yandex.ru)  
GitHub: [github.com/Dimontooos](https://github.com/Dimontooos)  
Проект: [ссылка на GitHub проекта](#)  

## О проекте Foodgram
Foodgram — это онлайн-платформа для:
- Публикации кулинарных рецептов
- Сохранения понравившихся рецептов
- Планирования покупок
- Вдохновения кулинарными идеями

### Функционал

#### Для авторизованных пользователей:
Создание/редактирование рецептов
Добавление в избранное
Список покупок (с возможностью скачивания)
Подписки на авторов
Управление профилем (смена пароля, аватарки)

#### Для гостей:
Просмотр рецептов
Поиск по сайту
Регистрация/авторизация

#### Администратору:
Полный доступ ко всем моделям
Расширенный поиск (по пользователям, рецептам, ингредиентам)
Статистика добавлений в избранное

## Установка и запуск

### 1. Настройка окружения
Создайте файл `infra/.env` со следующим содержимым:
```env
POSTGRES_USER=django
POSTGRES_PASSWORD=qwerty
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django-insecure-6&-%5ecbx&al2#xr!*@-og6al!kp8qcl%1_k7auy#i6e@(2+iz
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DEBUG=False

### 2. Работа с докером
docker-compose down -v --remove-orphans
docker-compose up -d --build

### 3. Инициализация базы данных
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py makemigrations recipes
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend python manage.py call_to_bd

### 4. Инициализация базы данных

Главная страница: http://localhost:8000/
Админ-панель: http://localhost:8000/admin/
Документация API: http://localhost:8000/api/docs/
