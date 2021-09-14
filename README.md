# Byshoes

Сервис парсинга обуви с сайтов, и отображения в едином виде.

##  Инструкция по настройке

1. Переименовать файл `docker-compose.override.example.yml` в `docker-compose.override.yml`
2. В файле `docker-compose.override.yml` изменить пароли и порты, время запуска парсинга на те которые нужны вам.
3. Запустить контейнеры командой `docker-compose up -d`.
4. Подключится к базе данных mongodb для настройки базы.
   1. Создайте базу командой `use byshoes`
   2. Создайте коллекцию командой `db.createCollection('byshoes-collection')`
   3. Создайте view командой:
   ```sh
   db.createView(
       "byshoes-latest",
       "byshoes-collection",
        [
          {$sort: {parsed: 1}}, 
          {$group: {
            _id: {$concat: ['$site', '$article']},
            id: {$last: '$_id'},
            title: {$last: '$title'},
            images: {$last: '$images'},
            images: {$last: '$link'},
            price: {$last: '$price'},
            discounted_price: {$last: '$discounted_price'},
            category: {$last: '$category'},
            specification: {$last: '$specification'},
            site: {$last: '$site'},
            article: {$last: '$article'},
            parsed: {$last: '$parsed'}
          }}
        ]
   )
   ```
   4. Создайте пользователя для базы данных командой. Не забудьте задать пароль указанный ранее в `docker-compose.override.yml`
   ```sh
   db.createUser({user: 'byshoes-user', pwd: '<PASSWORD>' , roles: [ { role: 'readWrite', db: 'byshoes' } ]})
   ```
5. Подождите запуска парсинга в автоматическом режиме или запустите его руками:
   1. Подключитесь к контейнеру командой `docker exec -it byshoes_byshoes-scheduler_1 sh`
   2. Запустите в контейнере скрипт парсинга `python manage.py startparse`
   3. Дождитесь окончания скрипта.
   4. Отключитесь от контейнера `exit`
6. В `docker-compose.override.yml` в блоке `mongodb` уберите блок `ports` для того чтобы отключить доступ к базе извне докера.
7. Примените изменения командой `docker-compose up -d`

В дальнейшем при необходимости работы напрямую с базой можно возвращать блок `ports` в контейнер `mongodb` база работает на порту `27017`

## Настройка времени запуска парсинга

Настройка времени запуска осуществляется указанием времени запуска в `docker-compose.override.yml`.
Необходимо изменять в контейнере `byshoes-scheduler` в блоке `env` параметры начинающиеся с `cron` (логика как в кроне).
Затем применить изменения `docker-compose up -d`.
