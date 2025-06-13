Работа выполнена 
Студентом Северо-кавказского федерального университета
Ардеевым Дмитрием Юрьевичем 
Обучающимся по направлению информационная безопасность автоматизированных сиситем 10.05.03 3 курса очной формы обучения.

Контактная почта:
ardeev.dima2020@yandex.ru

Ссылка на GitHub Аккаунт: https://github.com/Dimontooos
Ссылка на GitHub Проекта: 

Проект 
Foodgram — это онлайн-платформа, где пользователи могут делиться своими рецептами, находить вдохновение в кулинарных идеях других, а также удобно организовывать процесс готовки. 
Функционал проекта:

Для авторованных пользователей: главная страница, страницы других пользователей, страницы рецептов, подписка/отписка на страницы авторов, добавление/удаление рецептов в избранное, добавлние/удаление рецептов в список покупок, создание рецептов (публикация, удаление, редактирование), смена пароля, изменение/удаление аватрки, выход из аккаунта.

Для неавторизованных пользователей: Главная страница, страницы рецептов, страницы пользователей, формы входа и регистрации.

Для админки: просмотр всех пользователей по имени или email, поиск рецептов по названию и автору, отображените количество поиск ингредиентов по названию.

Перенд запуском проекта необходимо зайти в папку infra/ и создать файл .env, далее внести в него содержимое 

POSTGRES_USER=django
POSTGRES_PASSWORD=qwerty
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
SECRET_KEY=django-insecure-6&-%5ecbx&al2#xr!*@-og6al!kp8qcl%1_k7auy#i6e@(2+iz
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DEBUG=False

Для запуска докера проекта
docker-compose down -v --remove-orphans
docker-compose up -d --build

для запуска сайта
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py makemigrations recipes
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend python manage.py call_to_bd

Главная страница - http://localhost:8000/
Админ- http://localhost:8000/admin/
Документация - http://localhost:8000//api/docs/


