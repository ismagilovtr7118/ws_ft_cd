# ws_ft_cd
web service using [fastText](https://github.com/facebookresearch/fastText) to calculate the cosine distance between two texts in Russian

## Содержание

* [Что может](#Что-может)
* [Что используется для работы](#Что-используется-для-работы)
* [Инструкций по установке](#Инструкций-по-установке)
   * [Установка fastText](#Установка-fastText)
   * [Установка и настойка PostgreSQL](#Установка-и-настойка-PostgreSQL)

## Что может

* "/"
   * GET - выдается html страница с формой: два textarea (text1, text2) и кнопка потверждения.
   * POST - При нажатии на кнопку вычисляется косинусное расстояние между текстами (text1, text2), производится запись в базу данных, пользователю выдается значение.
* "/history" выдается html страница, на которой отображаются (с пагинацией) уже сделанные ранее запросы и их косинусные расстояния.
* "/similarities"
   * GET - выдает список с пагинацией уже сделанных ранее запросов косинусных расстояний в виде json.
   * POST - создает запрос на проверку косинусного расстояния, производится запись в базу данных, в ответ приходит созданный объект в виде json.
* "/similarities/<similarity_id>"
   * GET - выдает запрос косинусного расстояния с similarity_id в виде json.
   * PUT - редактирование запроса косинусного расстояния с <similarity_id>: text1, text2 - новое расстояние высчитывается, в ответ приходит измененный объект в виде json, новый запрос записывается в базу данных на позицию <similarity_id>
   * DELETE - удаление запроса косинусного расстояния с <similarity_id>. Возвращает сообщение о успешно выполненной операции

## Что используется для работы

* Python3
   * Flask
   * numpy
   * scipy
   * psycopg2
* PostgreSQL (Внимание! Данный проект не содержит готовую БД, установить и настроить её требуется самостоятельно. Инструкции ниже.)
* Docker
* [fastText](https://github.com/facebookresearch/fastText)
* [Модели для русского языка](http://docs.deeppavlov.ai/en/master/intro/pretrained_vectors.html#id2)

## Инструкций по установке

Проект создавался и тестировался на ОС Ubuntu 16.04 x64 и все команды представлены для неё.
Клонируем данный репозиторий и переходим в него
```
$ git clone https://github.com/ismagilovtr7118/ws_ft_cd.git
$ cd ws_ft_cd/
```

### Установка fastText

Переходим в каталог project
```
$ cd project/
```
или от корня
```
$ cd ws_ft_cd/project/
```
Клонируем проект [fastText](https://github.com/facebookresearch/fastText) и устанавливаем его по инструкции от разработчиков.
Должен отметить, что у меня безошибочно отработал только [Предпочтительный](https://github.com/facebookresearch/fastText#building-fasttext-using-make-preferred) способ. 
Способ установки через [cmake](https://github.com/facebookresearch/fastText#building-fasttext-using-cmake) завершился ошибкой.
В результате установки через [pip](https://github.com/facebookresearch/fastText#building-fasttext-for-python) не образовался столь необходимый в использовании файл fasttext, который позже всё-таки собрался при воспроизведении одного из примеров, но на это потребовалось время, да и в каталоге fastText образуются лишние каталоги с данными(data) и результатами(result) примеров, которые приходится вычищать, чтобы каталог весил меньше при сборке докер-образа.

### Установка и настойка PostgreSQL

Устанавливаем PostgreSQL
```
sudo apt-get install postgresql
```
Переходим к его настройке.
```
$ sudo vi /etc/postgresql/9.5/main/postgresql.conf
```
Нас интересует параметр listen_addresses устанавливаем его значение '0.0.0.0':
```
listen_addresses = '0.0.0.0'
```
Стоит обратить внимание на строку: "port = 5432" это стандартный порт для PostgreSQL.
Подключаемся к стандартной базе шаблонов PostgreSQL.
Меняем пароль пользователя postgres и выходим из БД.
```
$ sudo -u postgres psql template1
ALTER USER postgres with encrypted password 'your_password';
\q
```
Затем потребуется изменить ещё один файл:
```
$ sudo vi /etc/postgresql/9.5/main/pg_hba.conf
```
Настраиваем его следующим образом:
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     peer
# IPv4 local connections:
#host    all             all             127.0.0.1/32            md5
host    all             all             0.0.0.0/0               password
```
И перезапускаем, чтобы изменения вступили в силу
```
$ sudo /etc/init.d/postgresql restart
```
### Создание Базы данных и таблицы

Подключаемся к PostgreSQL.
Создаём базу данных
Подключаемся к ней
Создаём необходимую нам таблицу с id, полями для ввода текстов и полем для значения косинусного расстояния между ними.
```
$ psql -h localhost -U postgres
create database query_results_db
\c query_results_db;
query_results_db=# create table query_results(id serial primary key, text1 text, text2 text, cos_dist varchar(30));
```
Можно проверить, что всё получилось командой "\d"
Результат должен выглядеть следующим образом:
```
query_results_db=# \d
                  List of relations
 Schema |         Name         |   Type   |  Owner   
--------+----------------------+----------+----------
 public | query_results        | table    | postgres
 public | query_results_id_seq | sequence | postgres
(2 rows)
```
Теперь у нас есть БД, в которую будут сохраняться запросы.
