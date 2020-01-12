# ws_ft_cd
web service using [fastText](https://github.com/facebookresearch/fastText) to calculate the cosine distance between two texts in Russian

## Содержание

* [Что может](#Что может)
* [Что используется для работы](#Что используется для работы)
* [Инструкций по установке](#Инструкций по установке)

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
* PostgreSQL
* Docker
* [fastText](https://github.com/facebookresearch/fastText)
* [Модели для русского языка](http://docs.deeppavlov.ai/en/master/intro/pretrained_vectors.html#id2)

## Инструкций по установке
Клонируем данный репозиторий и переходим в него
```
$ git clone https://github.com/ismagilovtr7118/ws_ft_cd.git
$ cd ws_ft_cd/
```

