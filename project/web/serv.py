# -*- coding: utf-8 -*- 
from flask import Flask, flash, redirect, url_for
from flask import request
from flask import render_template
from flask import jsonify
from config import RECORDS_PER_PAGE, DATABASENAME, USER, PASSWORD, HOST, PORT
import os
import numpy as np
from scipy.spatial import distance
import psycopg2

app = Flask(__name__)
app.config.from_object('config')

ft_path = os.environ.get('FTPATH')
ft_model_name = os.environ.get('MODELNAME')

def readFile (fileName):
    f = open(fileName, 'r')
    words = f.readlines()
    return words

def save_file(fileName, text):
    with open(fileName, 'w') as file:
        file.write(text)

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

# предобработка данных
def preproc(words):
    for i in range(len(words)):
        words[i] = words[i].strip().split()
        words[i] = words[i][1:]
        for j in range(len(words[i])):
            words[i][j] = float(words[i][j])
        words[i] = np.array(words[i])
    return words

def calc_cos_dist(file1, file2):
    words1 = readFile(file1)
    words2 = readFile(file2)

    words1 = preproc (words1)
    words2 = preproc (words2)

    mean_words1 = np.mean(words1, axis=0)
    mean_words2 = np.mean(words2, axis=0)

    dist = distance.cosine(mean_words1, mean_words2)
    return dist

def fasttext(inFile, outFile):
    # Не нашёл инструкций по вызову fasttext напрямую из python
    cmd = 'cat '+ inFile +' | '+ ft_path +'fasttext print-word-vectors /opt/fastText/'+ ft_model_name +' > ' + outFile
    os.system (cmd)

def strs_to_dist(text1, text2):
    save_file('./web/txt/text1.txt', text1)
    save_file('./web/txt/text2.txt', text2)
    fasttext('./web/txt/text1.txt', 'text1vec.txt')
    fasttext('./web/txt/text2.txt', 'text2vec.txt')
    dist = calc_cos_dist('text1vec.txt', 'text2vec.txt')
    os.system ('rm -f ./web/txt/text1.txt ./web/txt/text2.txt text1vec.txt text2vec.txt')
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

def con_db():
    con = psycopg2.connect(
    database=DATABASENAME, 
    user=USER, 
    password=PASSWORD, 
    host=HOST, 
    port=PORT
    )
    print("Database opened successfully")
    return con

@app.route('/', methods=['GET', 'POST'])
def start_page():
    if request.method == 'POST':
        # Срабатывает при нажатии на кнопку и запускает расчёт косинусного расстояния между текстами
        form = request.form
        text1 = request.form.get('text1')
        text2 = request.form.get('text2')
        dist = strs_to_dist(text1, text2)
        con = con_db()
        cur = con.cursor()
        cur.execute("INSERT INTO query_results (text1, text2, cos_dist) VALUES ('"+ text1 +"', '"+ text2 +"', '"+ dist +"')")
        con.commit()  
        con.close()
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
    con = con_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM query_results")
    rows = cur.fetchall()
    records = get_records(rows)
    con.close()
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
    con = con_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM query_results")
    rows = cur.fetchall()
    records = get_records(rows)
    con.close()
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
        con = con_db()
        cur = con.cursor()
        cur.execute("INSERT INTO query_results (text1, text2, cos_dist) VALUES ('"+ text1 +"', '"+ text2 +"', '"+ dist +"')")
        con.commit()  
        con.close()
        print("Record inserted successfully")
        return jsonify(text1=text1, text2=text2, dist=dist)
    elif request.method == 'GET':
        # выдает список с пагинацией уже сделанных ранее запросов косинусных расстояний в виде json
        con = con_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM query_results")
        rows = cur.fetchall()
        records = get_records(rows)
        con.close()
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
    con = con_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM query_results")
    rows = cur.fetchall()
    records = get_records(rows)
    con.close()
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
        con = con_db()
        cur = con.cursor()
        cur.execute("UPDATE query_results SET text1 = '"+ text1 +"', text2 = '"+ text2 +"', cos_dist = '"+ dist +"' WHERE id=" + str(similarity_id))
        con.commit()  
        con.close()
        return jsonify(sim_id=similarity_id, text1=text1, text2=text2, dist=dist)
    elif request.method == 'GET':
        # выдает запрос косинусного расстояния с similarity_id в виде json 
        con = con_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM query_results WHERE id=" + str(similarity_id))
        rows = cur.fetchall()
        if len(rows) > 0:
            print ('len rows: ' + str(len(rows)))
            print (rows)
            id_qr = rows[0][0]
            txt1 = rows[0][1]
            txt2 = rows[0][2]
            cos_dist = rows[0][3]
            con.close()
            return jsonify(sim_id=id_qr, text1=txt1, text2=txt2, dist=cos_dist)
        else:
            con.close()
            return 'Ложки не существует' # Запрос к несуществующей записи
    elif request.method == 'DELETE':
        # удаление запроса косинусного расстояния с similarity_id
        con = con_db()
        cur = con.cursor()
        cur.execute("DELETE FROM query_results WHERE id=" + str(similarity_id))
        con.commit()  
        con.close()
        print("Record deleted successfully")
        return 'запись запроса %d удалена' % similarity_id
    else:
        # На случай непредвиденных ошибок
        return 'незапланированный REST-метод для similarities page %d' % similarity_id

if __name__ == '__main__':
    app.run(host='0.0.0.0')
