# -*- coding: utf-8 -*- 
from flask import Flask, flash, redirect, url_for
from flask import request
from flask import render_template
from flask import jsonify
from config import RECORDS_PER_PAGE
import os
from scipy.spatial import distance
import psycopg2
from FT_class import *
from peewee import *
from db_models import Query_results

app = Flask(__name__)
app.config.from_object('config')

ft_model_name = os.environ.get('MODELNAME')

ft = FT_class('/opt/fastText/'+ft_model_name)

db = Query_results() # Один раз создали объект БД

# Расчитывает параметры для страниц с пагинацией
# Получает полную историю, стартовую позицию от которой начать показ, текущий адрес страницы
def get_pag_list(history, st_pos, num_hist_page, page_type):
    if (st_pos+1 > len(history)): 
        return False, False, False # Нечего показывать, создаст пустую страницу истории
    else:
        if (st_pos+1+RECORDS_PER_PAGE <= len(history)):
            res = history[st_pos : st_pos+RECORDS_PER_PAGE]
            if (st_pos > 1):
                prev_page = str(st_pos-RECORDS_PER_PAGE+1) +"-"+  str(st_pos)
            else:
                prev_page = False
            if (st_pos+1+RECORDS_PER_PAGE == len(history)):
                next_page = False
            else:
                if (num_hist_page==None):
                    # Исключение для случая перенаправления с исходной страницы (/history или /similarities), когда ещё нет пеменной части
                    if (page_type=="hist"):
                        next_page = 'history/'+ str(st_pos+RECORDS_PER_PAGE+1) +"-"+ str(st_pos+2*RECORDS_PER_PAGE)
                    elif (page_type=="sim"):
                        next_page = 'similarities/'+ str(st_pos+RECORDS_PER_PAGE+1) +"-"+ str(st_pos+2*RECORDS_PER_PAGE)
                else:
                    next_page = str(st_pos+RECORDS_PER_PAGE+1) +"-"+ str(st_pos+2*RECORDS_PER_PAGE)
            return res, prev_page, next_page
        elif (st_pos+1+RECORDS_PER_PAGE > len(history)):
            res = history[st_pos:]
            if (len(history) > RECORDS_PER_PAGE):
                prev_page = str(st_pos-RECORDS_PER_PAGE+1) +"-"+ str(st_pos)
            else:
                prev_page = False
            next_page = False
            return res, prev_page, next_page

def strs_to_dist(text1, text2):
    vect1 = ft.give_a_vector(text1)
    vect2 = ft.give_a_vector(text2)
    dist = distance.cosine(vect1, vect2)
    return str(dist)

def get_records(rows):
    records = []
    for i in range(len(rows)):
        record = {}
        record["id"] = rows[i][0]
        record["text1"] = rows[i][1]
        record["text2"] = rows[i][2]
        record["cos_dist"] = rows[i][3]
        records.append(record)
    return records

# адаптация под рудимент программы. 
# Так были представлены данные в её первой версии (с сырыми запросами).
# Под такой формат заточен остальной код.
# Пришлось адаптировать с переходом на ORM.
def parse_q_res(q):
    hist = []
    for r in q:
        rec = {}
        rec['id'] = r.id
        rec['text1'] = r.text1
        rec['text2'] = r.text2
        rec['cos_dist'] = r.cos_dist
        hist.append(rec)
    return hist

@app.route('/', methods=['GET', 'POST'])
def start_page():
    if request.method == 'POST':
        # Срабатывает при нажатии на кнопку и запускает расчёт косинусного расстояния между текстами
        form = request.form
        text1 = request.form.get('text1')
        text2 = request.form.get('text2')
        dist = strs_to_dist(text1, text2)
        query = Query_results(text1=text1, text2=text2, cos_dist=dist)
        query.save()
        print("Record inserted successfully")
        flash(dist)
        return render_template('start_page.html')
    elif request.method == 'GET':
        # Выдаёт страницу для ввода текстов и кнопку отправки запроса
        return render_template('start_page.html')
    else:
        # На случай непредвиденных ошибок
        return 'незапланированный REST-метод'

# Реализовал пагинацию через переменную часть URL
@app.route('/history/<path:hist_id>')
def hist_id_page(hist_id):
    q = Query_results.select()
    records = parse_q_res(q)
    arr_hist_id = hist_id.split("-")
    printable_records, prev_page, next_page = get_pag_list(records, int(arr_hist_id[1])-RECORDS_PER_PAGE, hist_id, "hist")
    if (printable_records != False):
        return render_template('history.html', records=printable_records, prev_page=prev_page, next_page=next_page)
    else:
        return render_template('history.html')

# выдает список с пагинацией уже сделанных ранее запросов косинусных расстояний в виде json
# аналогична /history/"1-"+str(RECORDS_PER_PAGE-1)
@app.route('/history')
def hist_page():
    q = Query_results.select()
    records = parse_q_res(q)
    printable_records, prev_page, next_page = get_pag_list(records, 0, None, "hist")
    if (printable_records != False):
        return render_template('history.html', records=printable_records, prev_page=prev_page, next_page=next_page)
    else:
        return render_template('history.html')

@app.route('/similarities', methods=['GET', 'POST'])
def similar_page():
    if request.method == 'POST':
        #'создает запрос на проверку косинусного расстояния, в ответ приходит созданный объект в виде json'
        text1 = request.form.get('text1')
        text2 = request.form.get('text2')
        dist = strs_to_dist(text1, text2)
        query = Query_results(text1=text1, text2=text2, cos_dist=dist)
        query.save()
        return jsonify(text1=text1, text2=text2, dist=dist)
    elif request.method == 'GET':
        # выдает список с пагинацией уже сделанных ранее запросов косинусных расстояний в виде json
        q = Query_results.select()
        records = parse_q_res(q)
        printable_records, prev_page, next_page = get_pag_list(records, 0, None, "sim")
        if (printable_records != False):
            return render_template('similarities.html', records=printable_records, prev_page=prev_page, next_page=next_page)
        else:
            return render_template('similarities.html')
    else:
        # На случай непредвиденных ошибок
        return 'незапланированный REST-метод'

# Реализовал пагинацию через переменную часть URL
# аналогична /similarities/"1-"+str(RECORDS_PER_PAGE-1)
@app.route('/similarities/<path:hist_id>')
def sim_id_page(hist_id):
    q = Query_results.select()
    records = parse_q_res(q)
    arr_hist_id = hist_id.split("-")
    printable_records, prev_page, next_page = get_pag_list(records, int(arr_hist_id[1])-RECORDS_PER_PAGE, hist_id, "sim")
    if (printable_records != False):
        return render_template('similarities.html', records=printable_records, prev_page=prev_page, next_page=next_page)
    else:
        return render_template('similarities.html')

@app.route('/similarities/<int:similarity_id>', methods=['GET', 'PUT', 'DELETE'])
def similar_id_page(similarity_id):
    if request.method == 'PUT':
        # редактирование запроса косинусного расстояния с similarity_id: text1, text2 - новое расстояние высчитывается, в ответ приходит измененный объект в виде json'
        text1 = request.form.get('text1')
        text2 = request.form.get('text2')
        dist = strs_to_dist(text1, text2)
        q = Query_results.get_or_none(Query_results.id == similarity_id)
        q.text1 = text1
        q.text2 = text2
        q.cos_dist = dist
        q.save()
        return jsonify(sim_id=similarity_id, text1=text1, text2=text2, dist=dist)
    elif request.method == 'GET':
        # выдает запрос косинусного расстояния с similarity_id в виде json
        q = Query_results.select().where(Query_results.id == similarity_id)
        res = parse_q_res(q)
        if len(res) > 0:
            return res[0]
        else:
            return 'Ложки не существует' # Запрос к несуществующей записи
    elif request.method == 'DELETE':
        # удаление запроса косинусного расстояния с similarity_id
        q = Query_results.get_or_none(Query_results.id == similarity_id)
        q.delete_instance()
        print("Record deleted successfully")
        return 'запись запроса %d удалена' % similarity_id
    else:
        # На случай непредвиденных ошибок
        return 'незапланированный REST-метод для similarities page %d' % similarity_id

if __name__ == '__main__':
    app.run(host='0.0.0.0')
