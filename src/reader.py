# -*- coding: utf-8 -*-
import  re
import  requests
import  json
import  sqlite3
import  datetime
# ======================================================================================================================
from    src.tools           import  tools                   as  t
from    src                 import  globals                 as  g
from    src.dictionaries    import  dictionary              as  d
# ======================================================================================================================
class reader():
    # переменные для символов разделителей объявлены здесь:
    rv                                                      =   'ꡦ'                                                     # RecordValue - раньше был символ ·, а теперь будет Пагба-ламы буква ee U+A866 https://unicode-table.com/ru/A866/ #case 2020.05.21
    nr                                                      =   'ꡗ'                                                     # NewSubrecord - раньше был символ ¦, а теперь будет U+A877(꡷) Пагба-ламы знак двойной шэд https://unicode-table.com/ru/A877/ #case 2020.05.21    
    nl                                                      =   'ꡗ'                                                     # NewRecord - раньше был символ ¿, а теперь будет  ꡗ Пагба-ламы буква ya U+A857 https://unicode-table.com/ru/A857/ #case 2020.05.21
    nf                                                      =   'ꡅ'                                                     # NumFound - раньше был символ Ї, а теперь будет   ꡅ Пагба-ламы буква cha U+A845 #case 2020.05.21
    # ------------------------------------------------------------------------------------------------------------------
    # полная процедура разбора запроса, выбора данных из solr, кодирования результата и его возврата
    # ------------------------------------------------------------------------------------------------------------------
    def full_proceess_read(query):
        ##### limitation start
        #import platform
        #if not platform.node().upper()  in ['CDC-1CL-REP-01','DESKTOP-L608GJN','1C-01']: return
        ##### limitation end
        try:
            fpr_ret                                         =   ''
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # разбор запроса
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            solr_json_query                                 =   reader.build_solr_query(query)                          # вот и весь разбор - формирую текст запроса данных в Solr
            ib                                              =   re.findall(r'ref=(.*?)(?=\&)',query)[0]                 # имя базы мне нужно и здесь
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # выбора данных из solr
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            json_data                                       =   json.dumps(solr_json_query)
            json_data                                       =   json_data.replace('\\"\\"','\\"')                       # убираю двойные кавычки из запросов (dumps добавляет кавычки строкам с пробемами, а без пробелом не добавляет. Поэтому я сам добавляю кавычки ко все строкам, а здесь убираю задвоенные
            json_data                                       =   json_data.replace('\\"*\\"','\\"*')                     # и такую херь надо вычичать тоже
            url                                             =   g.execution.solr.url_main + "/" + \
                                                                t.normalize_ib_name(ib) + \
                                                                "/select"
            headers                                         =   {'content-type': 'application/json'}
        except Exception as e:
            t.debug_print("fail on json_data "+str(e))
        try:
            r                                               =   requests.post(url, data=json_data, headers=headers)
            if r.status_code                                !=  200:
                #return r.content                                                                                           # это только для отладки
                t.debug_print("url is " + url + "\r\njson data is" + str(json_data))
                return "Ошибка при обработке запроса. Код возврата "+str(r.status_code)
        except Exception as e:
            return "Ошибка при обработке запроса:"+str(e)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # чтение отобранных данных
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        fpr_exp                                             =   ""
        try:
            fpr_exp                                         =   "json.loads"
            fpr_json                                        =   json.loads(r.content.decode(encoding='UTF8'))
            fpr_exp                                         =   "json.get"
            if fpr_json.get('response'):
                fpr_exp                                     =   "json.get.docs"
                if fpr_json['response'].get('docs'):
                    data                                    =   []
                    fname                                   =   ""
                    fpr_exp                                 =   "get_parsed_size"
                    p_sz                                    =   reader.get_parsed_size(
                                                                    t.normalize_ib_name(ib)
                                                                )
                    fpr_exp                                 =   "get_total_size"
                    t_sz                                    =   reader.get_total_size(
                                                                    t.normalize_ib_name(ib)
                                                                )
                    t_sz                                    =   t_sz if t_sz > 0 else 1
                    fpr_exp                                 =   "fpr_ret 1"
                    fpr_ret                                 +=  str(int(p_sz / t_sz * 100)) + ':'                       # alt+? сначала процент, потом двоеточие
                    fpr_exp                                 =   "fpr_ret 2"
                    fpr_ret                                 +=  str(fpr_json['response']['numFound']) + reader.nf       #<strike> alt+? потом общее количество документов</strike> #case 2020.05.21
                    fpr_exp                                 =   "is_ib_is_lgd"
                    if reader.is_ib_is_lgd(
                        t.normalize_ib_name(ib)
                    ):                                                                                                  # читаем данные в зависимости от типа ЖР
                        ids                                 =   []                                                      # здесь будет жить список rowID
                        fpr_exp                             =   "reversed(fpr_json) 1"
                        for each                            in  reversed(fpr_json['response']['docs']):
                            fname                           =   each.get('id')
                            ids.append(each.get('pos'))
                        fpr_exp                             =   "read_lgd_data"
                        data                                =   reader.read_lgd_data(
                                                                                    t.get_file_by_id(
                                                                                                    fname
                                                                                    )
                                                                                    ,ids)                               # здесь мы выбираем все rowID
                    else:
                        fpr_exp                             =   "reversed(fpr_json) 2"
                        for each                            in  reversed(fpr_json['response']['docs']):                 # так как у меня выбрано с конца, то переворачиваю массив
                            fpr_exp                         =   "read_lgp_data"
                            data.append(reader.read_lgp_data(each,ib))
                    fpr_exp                                 =   "data:"
                    if data:
                        fpr_exp                             =   "each data:"
                        for each                            in data:                                                    # здесь формирую ответ для обработки
                            fpr_exp                         =   "reader.prepare_for_1c"
                            fpr_ret                         +=  reader.prepare_for_1c(
                                                                t.normalize_ib_name(ib),
                                                                each)
                else:
                    fpr_ret                                 =   'Нет данных, соответствующих данному отбору'
                    t.debug_print(ib+":"+fpr_ret,'reader()')
            else:
                fpr_ret                                     =   'Ответ не получен'
                t.debug_print(ib+":"+fpr_ret, 'reader()')
        except Exception as e:
            t.debug_print("fail on preparing data "+str(e)+" str is "+fpr_exp, 'reader()')
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        return fpr_ret
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ------------------------------------------------------------------------------------------------------------------
    # читаем запись старого формата
    # ------------------------------------------------------------------------------------------------------------------
    def read_lgd_data(rld_file,items):
        # чтение и декодирование записи ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        parsed                                             =   t.sqlite3_exec(rld_file,'''Select                                       
                                                                    date,
                                                                    transactionStatus, 
                                                                    transactionDate,
                                                                    transactionID,
                                                                    userCode,
                                                                    computerCode,
                                                                    appCode,
                                                                    connectID,
                                                                    eventCode,
                                                                    severity,
                                                                    comment,
                                                                    metadataCodes,
                                                                    data,
                                                                    dataPresentation,
                                                                    workServerCode,
                                                                    primaryPortCode,
                                                                    secondaryPortCode,
                                                                    session
                                                                    from    EventLog
                                                                    Where RowID in ''' + \
                                                                    str(items).replace('[','(').replace(']',')'))       # выбираю сразу всю пачку
        ret                                                 =   []
        if not parsed:
            return
        for elem                                            in parsed:
            data                                            =   {}
            data[0]                                         =   reader.int_1c_time_to_old_zhr_time(elem[0],islgd=True)  # исправляю дату
            data[1]                                         =   reader.trans_descr(d.trans_state[str(elem[1])])         # записываю статус транзакции строкой
            data[2]                                         =   reader.int_1c_time_to_human_string(elem[2],islgd=True)\
                                                            +   " ("+str(elem[3])+")"
            data[4]                                         =   str(elem[4])                                            # r4 - пользователь
            data[5]                                         =   str(elem[5])
            data[6]                                         =   str(elem[6])
            data[7]                                         =   str(elem[7])
            data[8]                                         =   str(elem[8])
            data[9]                                         =   reader.rec_descr(d.severity[str(elem[9])])
            data[10]                                        =   str(elem[10])
            data[11]                                        =   str(elem[11])
            try:
                data12                                      =   g.rexp.del_quotes.sub('',str(elem[12]))                 #-кавычки в начале и конце
                data12                                      =   reader.force_decode(data12)
                if      re.findall(r'^\{\"P\",',data12):
                    data12                                  =   re.sub(r'^\{|\}$','',data12)                            # убираем {} скобки
                elif    g.rexp.find_1c_link.findall(data12):
                    data12                                  =   re.sub(r'([\w\d]+\:[\w\d]+)', '"R",' + r'\1', data12)   # дописываем R к ссылке
                elif    data12:
                    data12                                  =   '"S","'+data12+'"'                                      # дописываем S к строке
                else:
                    data12                                  =   '"U"'                                                   # пустая строка
            except Exception as e:
                t.debug_print("Exception12 "+str(e))
                data12                                      =   str(e)
            data[12]                                        =   data12
            #t.debug_print(data[12])
            data[13]                                        =   str(elem[13])
            data[14]                                        =   str(elem[14])
            data[15]                                        =   str(elem[15])
            data[16]                                        =   str(elem[16])
            data[17]                                        =   str(elem[17])
            ret.append(data)                                                                                            # добавлю очередную запись в возвращаемый массив
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # читаем запись нового формата
    # ------------------------------------------------------------------------------------------------------------------
    def read_lgp_data(rld_rec,rld_base):
        data                                                =   {}
        rld_excp                                            =   ""
        try:
            # чтение и декодирование записи ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            rld_excp                                        =   "open"
            f                                               =   open(
                                                                    t.get_file_by_id(
                                                                                    rld_rec.get('id')
                                                                                    )
                                                                    ,'rb')
            rld_excp                                        =   "seek"
            f.seek(rld_rec.get('pos'))
            rld_excp                                        =   "read"
            raw                                             =   f.read(rld_rec.get('len')).decode(encoding='UTF8')
            f.close()
            rld_excp                                        =   "parse"
            parsed                                          =   g.rexp.my_sel_re.findall(raw)
            rld_excp                                        =   "data"
            data[0]                                         =   parsed[0][0]                                            # записываю статус транзакции строкой
            rld_excp                                        =   "tran_fix"
            if(parsed[0][8]                                 in  g.execution.c1_dicts.tran_fix_list[
                                                                t.normalize_ib_name(rld_base)
                                                                ]):                                                     # и операция нужнается в корректировке типа транзакции
                rld_excp                                    =   "tran_descr 1"
                data[1]                                     =   reader.trans_descr(parsed[0][1], fix=True)              # записываю статус с поправкой
            else:
                rld_excp                                    =   "tran_descr 2"
                data[1]                                     =   reader.trans_descr(parsed[0][1])                        # записываю статус транзакции строкой без поправки
            rld_excp                                        =   "time conversion"
            data[2]                                         =   reader.hex_1c_time_to_human_string(parsed[0][2]) + \
                                                                                " ("+str(int(parsed[0][3],16))+")"
            for li in range(4,9):
                data[li]                                    =   parsed[0][li]                                            # событие
            rld_excp                                        =   "rec descr"
            data[9]                                         =   reader.rec_descr(parsed[0][9])                          # важность
            for li in range(10,18):
                data[li]                                    =   parsed[0][li]
            if len(parsed[0])                               >   g.rexp.sel_re_ext_nmb :                                 #case 2020.05.21
                data[18]                                    =   parsed[0][20]                                           #case 2020.05.21
                data[19]                                    =   parsed[0][21]                                           #case 2020.05.21
            else:                                                                                                       #case 2020.05.21
                data[18]                                    =   0                                                       #case 2020.05.21
                data[19]                                    =   0                                                       #case 2020.05.21
        except Exception as e:
            t.debug_print("read lgp failed on "+rld_excp+" with "+str(e),"reader")
            data                                            =   None
        return data
    # ------------------------------------------------------------------------------------------------------------------
    # Готовим запись для чтения обработкой 1С
    # ------------------------------------------------------------------------------------------------------------------
    def prepare_for_1c(rr_ib,flds):
        rr_ret                                              =   ""
        try:
            #t.debug_print(data+'\n============================================================================\n')
            # разбираю записи ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if len(flds)                                    >   0:                                                      # <strike>· - alt+0183, ¦ - alt+0166, ¿ - alt+0191</strike>
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R1"        + reader.rv + flds[0]           + reader.nr # R1 - Дата #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #1 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R2"        + reader.rv + flds[1]           + reader.nr # R2 - тип транзакции #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #2 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R3"        + reader.rv + flds[2]           + reader.nr # R3 - время транзакции и её ID #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #3 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r4                                      =   d.get_complex_rec(
                                                                    g.execution.c1_dicts.users[rr_ib],
                                                                    flds[4]
                                                                )
                except Exception as e:
                    t.debug_print("Exception: prepare #4a error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R4int"     + reader.rv + r4['uuid']        + reader.nr # R4int - uuid пользователя #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #4i error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R4"        + reader.rv + r4['name']        + reader.nr # R4 - имя пользователя #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #4 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R5"        + reader.rv + d.get_simple_descr(
                                                                                g.execution.c1_dicts.computers[rr_ib],
                                                                                flds[5]
                                                                              )                             + reader.nr # R5 - имя компьютера #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #5 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r6int                                   =   d.get_simple_descr(
                                                                    g.execution.c1_dicts.applications[rr_ib],
                                                                    flds[6]
                                                                )
                except Exception as e:
                    t.debug_print("Exception: prepare #6i error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r6                                      =   d.clients.get(r6int)            \
                                                                if d.clients.get(r6int) else    \
                                                                r6int
                except Exception as e:
                    r6                                      =   'Ошибка разбора'
                    t.debug_print("Exception: prepare #6a error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R6"        + reader.rv + r6                + reader.nr # R6 - имя приложения #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #6 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R6int"     + reader.rv + r6int             + reader.nr # R6int - имя во внутреннем представлении #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #6i2 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R7"        + reader.rv + str(flds[7])      + reader.nr # R7 - id соединения #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #7 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r8                                      =   d.get_simple_descr(
                                                                    g.execution.c1_dicts.actions[rr_ib],
                                                                    flds[8]
                                                                )                                                       # получаю description события. Это может быть как результат, так и элемент справочника предопределённых событий
                except Exception as e:
                    t.debug_print("Exception: prepare #8a error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r8                                      =   d.actions.get(r8) \
                                                                if d.actions.get(r8) \
                                                                else r8
                except Exception as e:
                    t.debug_print("Exception: prepare #8b error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R8"        + reader.rv + r8                + reader.nr # R8 - событие. Вот здесь всё уже будет хорошо. #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #8 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R9"        + reader.rv + flds[9]           + reader.nr # R9 - уровень события. #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #9 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R10"       + reader.rv + flds[10]           + reader.nr # R10 - комментарий #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #10 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r11                                     =   d.get_complex_rec(
                                                                    g.execution.c1_dicts.metadata[rr_ib],
                                                                    flds[11]
                                                                )
                except Exception as e:
                    t.debug_print("Exception: prepare #11a error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R11"       + reader.rv + r11.get('name')   + reader.nr # R11 - метаданные #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #11b error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R11int"    + reader.rv + r11.get('name')   + reader.nr # R11int - метаданные, внутренне представление. Отдаю то же самое. Так должно быть. #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #11i error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R12"       + reader.rv + flds[12]          + reader.nr # R12 - данные #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #12 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R13"       + reader.rv + flds[13]          + reader.nr # R13 - представление данных #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #13 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R14"       + reader.rv + d.get_simple_descr(
                                                                                    g.execution.c1_dicts.servers[rr_ib],
                                                                                    flds[14]
                                                                                )                           + reader.nr # R14 - имя сервера #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #14 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r15                                     =   d.get_simple_descr(
                                                                    g.execution.c1_dicts.ports_main[rr_ib],
                                                                    flds[15]
                                                                )
                except Exception as e:
                    t.debug_print("Exception: prepare #15a error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r15                                     =   r15 if r15  else "0"                                    # чтобы значение не было пустым, надо сделать его нулевым
                except Exception as e:
                    t.debug_print("Exception: prepare #15b error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R15"       + reader.rv + r15               + reader.nr # R15 - Основной порт
                except Exception as e:
                    t.debug_print("Exception: prepare #15 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r16                                     =   d.get_simple_descr(
                                                                    g.execution.c1_dicts.ports_add[rr_ib],
                                                                    flds[16]
                                                                )
                except Exception as e:
                    t.debug_print("Exception: prepare #16a error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    r16                                     =   r16 if r16  else "0"                                    # чтобы значение не было пустым, надо сделать его нулевым
                    rr_ret                                  +=  "R16"       + reader.rv + r16               + reader.nr # R16 - дополнительный порт
                except Exception as e:
                    t.debug_print("Exception: prepare #16 error:"+str(e))
                # ------------------------------------------------------------------------------------------------------
                try:
                    rr_ret                                  +=  "R17"       + reader.rv + flds[17]          + reader.nr # R17 - номер сеанса #case 2020.05.21
                except Exception as e:
                    t.debug_print("Exception: prepare #17 error:"+str(e))
                try:                                                                                                    #case 2020.05.21
                    if len(flds)> g.rexp.sel_re_ext_nmb:                                                                #case 2020.05.21
                        rr_ret                              +=  "R18"       + reader.rv + flds[21]          + reader.nr # R18 - разделение данных из поля R21, основные данные  #case 2020.05.21
                        rr_ret                              +=  "R19"       + reader.rv + flds[22]          + reader.nl # R19 - разделение данных из поля R22 , вспомогательные данные   #case 2020.05.21
                    else:                                                                                               #case 2020.05.21
                        rr_ret                              +=  "R18"       + reader.rv + "0"               + reader.nr\
                                                            +   "R19"       + reader.rv + "0"               + reader.nl #case 2020.05.21
                except Exception as e:                                                                                  #case 2020.05.21
                    t.debug_print("Exception: prepare #(18)21-(19)#22 error:"+str(e))
            else:
                t.debug_print('invalid  record  =' + str(flds),'reader.prepare_for_1c')
        except Exception as e:
            t.debug_print("Prepare exception:"+str(e),'reader.prepare_for_1c')
            rr_ret                                          =   ""
        return rr_ret
    # ------------------------------------------------------------------------------------------------------------------
    # возвращает описания типа транзакции по её букве
    # ------------------------------------------------------------------------------------------------------------------
    def trans_id(td_descr):
        td_str                                              =   ''
        td_descr                                            =   td_descr.upper()
        if td_descr                                         ==  'НЕТ ТРАНЗАКЦИИ': td_str =  'N'
        if td_descr                                         ==  'ЗАФИКСИРОВАНА' : td_str =  'U'
        if td_descr                                         ==  'НЕ ЗАВЕРШЕНА'  : td_str =  'R'
        if td_descr                                         ==  'ОТМЕНЕНА'      : td_str =  'C'
        return td_str
    # ------------------------------------------------------------------------------------------------------------------
    # возвращает описания типа транзакции по её букве
    # ------------------------------------------------------------------------------------------------------------------
    def trans_descr(td_lttr,fix=False):
        td_str                                              =   ''
        td_lttr                                             =   td_lttr.replace("'","")
        if fix:
            if td_lttr                                      ==  'C':
                td_lttr                                     =   'U'
            elif td_lttr                                    ==  'R':
                td_lttr                                     =   'C'
            elif td_lttr                                    ==  'U':
                td_lttr                                     =   'R'
        if td_lttr                                          ==  'N': td_str =   'Нет Транзакции'                        # регистр
        if td_lttr                                          ==  'C': td_str =   'Отменена'                              # имеет
        if td_lttr                                          ==  'R': td_str =   'Не Завершена'                          # важное
        if td_lttr                                          ==  'U': td_str =   'Зафиксирована'                         # значение
        return td_str
    # ------------------------------------------------------------------------------------------------------------------
    # возвращает ID типа записи по описанию
    # ------------------------------------------------------------------------------------------------------------------
    def rec_descr_id(rd_descr):
        rd_str                                              =   ''
        rd_descr                                            =   rd_descr.upper()
        if rd_descr                                         ==  'ИНФОРМАЦИЯ'    : rd_str =  'I'
        if rd_descr                                         ==  'ПРЕДУПРЕЖДЕНИЕ': rd_str =  'W'
        if rd_descr                                         ==  'ОШИБКА'        : rd_str =  'E'
        if rd_descr                                         ==  'ПРИМЕЧАНИЕ'    : rd_str =  'N'
        return rd_str
    # ------------------------------------------------------------------------------------------------------------------
    # возвращает описания типа записи
    # ------------------------------------------------------------------------------------------------------------------
    def rec_descr(rd_lttr):
        rd_str                                              =   ''
        if rd_lttr                                          ==  'I': rd_str =   'Информация'
        if rd_lttr                                          ==  'E': rd_str =   'Ошибка'
        if rd_lttr                                          ==  'W': rd_str =   'Предупреждение'
        if rd_lttr                                          ==  'N': rd_str =   'Примечание'
        return rd_str
    # ------------------------------------------------------------------------------------------------------------------
    # функция конвертации даты из последовательности в форматированную строку
    # ------------------------------------------------------------------------------------------------------------------
    def date_to_zhr_date(dtzd_date):
        dtzd_re                                             =   re.compile(r'(\d+)\.(\d+)\.(\d+)\s+(\d+)\:(\d+)\:(\d+)')
        dtzd_res                                            =   dtzd_re.findall(dtzd_date);
        dtzd_year                                           =   str(dtzd_res[0][2])
        dtzd_mon                                            =   str(dtzd_res[0][1])
        if (len(dtzd_mon)                                   ==  1):
            dtzd_mon                                        =   "0"+dtzd_mon
        dtzd_day                                            =   str(dtzd_res[0][0])
        if (len(dtzd_day)                                   ==  1):
            dtzd_day                                        =   "0"+dtzd_day
        dtzd_hour                                           =   str(dtzd_res[0][3])
        if (len(dtzd_hour)                                  ==  1):
            dtzd_hour                                       =   "0"+dtzd_hour
        dtzd_min                                            =   str(dtzd_res[0][4])
        if (len(dtzd_min)                                   ==  1):
            dtzd_min                                        =   "0"+dtzd_min
        dtzd_sec                                            =   str(dtzd_res[0][5])
        if (len(dtzd_sec)                                   ==  1):
            dtzd_sec                                        =   "0"+dtzd_sec
        return dtzd_year+dtzd_mon+dtzd_day+dtzd_hour+dtzd_min+dtzd_sec
    # ------------------------------------------------------------------------------------------------------------------
    # формирую текст запросы данных у Solr
    # ------------------------------------------------------------------------------------------------------------------
    def build_solr_query(bsq_query):
        # определяю переменные ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ib_name                                             =   ""                                                      # здесь лежит имя базы из запроса
        bsq_amount                                          =   ""                                                      # количество отбираемых записей
        bsq_date_start                                      =   ""                                                      # отбор по дате - это начало
        bsq_date_end                                        =   ""                                                      # отбор по дате - это конец
        bsq_status_trans                                    =   ""                                                      # r2 отбор по статусу транзакции
        bsq_users                                           =   ""                                                      # r4 отбор по пользователям
        bsq_computers                                       =   ""                                                      # r5 отбор по компьютерам
        bsq_applications                                    =   ""                                                      # r6 отбор по приложению
        bsq_actions                                         =   ""                                                      # r8 сюда наберу все отбираемые события
        bsq_levels                                          =   ""                                                      # r9 уровень важности
        bsq_comments                                        =   ""                                                      # r10 сводный фильтр по комментариям
        bsq_metadatas                                       =   ""                                                      # r11 отбор по метаданным
        bsq_datas                                           =   ""                                                      # r12 отбор по данным
        bsq_data_presentations                              =   ""                                                      # r13 отбор по представлению метаданных
        bsq_servers                                         =   ""                                                      # r14 отбор по серверам
        bsq_main_ports                                      =   ""                                                      # r15 отбор по основным портам
        bsq_add_ports                                       =   ""                                                      # r16 отбор по дополнительным портам
        bsq_seanses                                         =   ""                                                      # r17 отбор по номеру сеанса
        bsq_ext_main                                        =   ""                                                      # r18(21) отбор по основному разделителю #case 2020.05.21
        bsq_ext_add                                         =   ""                                                      # r19(22) отбор по дополнительному разделителю #case 2020.05.21

        # сначала определяю имя базы ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for ref in g.rexp.q.ref_re.findall(bsq_query):
            ref                                             =   t.normalize_ib_name(ref)
            d.read_ib_dictionary(ref)                                                                                   # здесь прочитаю словарь
            ib_name                                         =   ref
        # все параметры по очереди ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for param                                           in  bsq_query.split('&'):                                   # прохожусь по всем параметрам
            # r1 - устанавливаю отбор по датам ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for date_start                                  in  g.rexp.q.date_start.findall(param):
                bsq_date_start                              =   reader.date_to_zhr_date(date_start)
            for date_stop                                   in  g.rexp.q.date_end.findall(param):
                bsq_date_end                                =   reader.date_to_zhr_date(date_stop)
            # r2 - отбор по статусу транзакции ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for tran                                        in g.rexp.q.trans_status_re.findall(param):
                bsq_status_trans                            +=  "r2:"   +   reader.trans_id(tran)               + " || "# формирую отбор по статусу транзакции
            # r3 - отбор транзакции ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # r4 - отбор по пользователю ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for user                                        in  g.rexp.q.user_re.findall(param):
                if g.rexp.uuid_start.match(user):
                    bsq_users                               +=  "r4:"   +   d.get_complex_id(
                                                                                g.execution.c1_dicts.users[ib_name],
                                                                                gcr_uuid    =   user
                                                                            )                                   + " || "# формирую отбор по UUID пользователя
                else:
                    bsq_users                               +=  "r4:"   +   d.get_complex_id(
                                                                                g.execution.c1_dicts.users[ib_name],
                                                                                gcr_name    =   user
                                                                            )                                   + " || "# формирую отбор по имени пользователя
            # r5 - отбор по компьютерам ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for computer                                    in  g.rexp.q.computer_re.findall(param):
                bsq_computers                               +=  "r5:"   +   d.get_simple_id(
                                                                                g.execution.c1_dicts.computers[ib_name],
                                                                                computer
                                                                            )                                   + " || "# формирую отбор по компьютеру
            # r6 - отбор по приложению ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for application                                 in g.rexp.q.application_re.findall(param):
                bsq_applications                            +=  "r6:"   +   d.get_simple_id(
                                                                                g.execution.c1_dicts.applications[ib_name],
                                                                                application
                                                                            )                                   + " || "# формирую отбор по приложению
            # r8 - пройдусь по событиям ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for action                                      in  g.rexp.q.action_re.findall(param):
                for each                                    in  d.actions:
                    action                                  =   each if d.actions[each] ==  action else action          # если это предопределённый action из словаря, то выбираем его внутреннее представление
                bsq_actions                                 +=  "r8:"   +   d.get_simple_id(
                                                                                g.execution.c1_dicts.actions[ib_name],
                                                                                action
                                                                            )                                   + " || "# формирую отбор по событиям
            # r9 - отбор по уровню важности ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for level                                       in g.rexp.q.level_re.findall(param):
                bsq_levels                                  +=  "r9:"   +   reader.rec_descr_id(level)          + " || "# формирую отбор по уровеню события
            # r10 - отбор по комментарию ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for comment                                     in  g.rexp.q.comments_re.findall(param):
                bsq_comments                                +=  "r10:"  +   '"*'+comment+'*"'                   + " || "# отбор по комментарию
            # r11 - отбор по метаданным ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for metadata                                    in  g.rexp.q.metadata_re.findall(param):
                if g.rexp.uuid_start.match(metadata):
                    bsq_metadatas                           +=  "r11:"  +   d.get_complex_id(
                                                                                g.execution.c1_dicts.metadata[ib_name],
                                                                                gcr_uuid    =   metadata
                                                                            )                                   + " || "# отбор по GUID метаданных
                else:
                    bsq_metadatas                           +=  "r11:"  +   d.get_complex_id(
                                                                                g.execution.c1_dicts.metadata[ib_name],
                                                                                gcr_name    =   metadata
                                                                            )                                   + " || "# отбор по имени метаданных
            # r12 - отбор по данным ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for data                                        in  g.rexp.q.data_re.findall(param):
                bsq_datas                                   +=  "r12:"  +   '"*'+data+'*"'                      + " || "# отбор по данным
            # r13 - отбор по представлению данных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for data_presentation                           in  g.rexp.q.data_presentation_re.findall(param):
                bsq_data_presentations                      +=  "r13:"  +   '"*'+data_presentation+'*"'         + " || "# отбор по представлению данных
            # r14 - отбор по серверам ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for server                                      in  g.rexp.q.server_re.findall(param):
                bsq_servers                                 +=  "r14:"  +   d.get_simple_id(
                                                                                g.execution.c1_dicts.servers[ib_name],
                                                                                server
                                                                            )                                   + " || "# отбор по серверам
            # r15 - отбор по основному порту ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for main_port                                   in  g.rexp.q.port_main_re.findall(param):
                bsq_main_ports                              +=  "r15:"  +   d.get_simple_id(
                                                                                g.execution.c1_dicts.ports_main[ib_name],
                                                                                re.sub(r'\s+','',main_port)
                                                                            )                                   + " || "# отбор по главным портам
            # r16 - отбор по дополнительному порту ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for add_port                                    in  g.rexp.q.port_add_re.findall(param):
                bsq_add_ports                               +=  "r16:"  +   d.get_simple_id(
                                                                                g.execution.c1_dicts.ports_add[ib_name],
                                                                                re.sub(r'\s+', '', add_port)
                                                                            )                                   + " || "# отбор по дополнительному порту
            # r17 - отбор по сеансу ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for seanse                                      in  g.rexp.q.seans_re.findall(param):
                bsq_seanses                                 +=  "r17:"  +   seanse                              + " || "# отбор по сеансу.
            # r18 - отбор по разделению основных данных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#case 2020.05.21
            for ext_main_nmb                                in  g.rexp.q.ext_main.findall(param):                       #case 2020.05.21
                bsq_ext_main                                +=  "r18:"  +   ext_main_nmb                        + " || "# отбор по разделению основных данных.#case 2020.05.21
            # r19 - отбор по разделению дополнительных данных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#case 2020.05.21
            for ext_ext_nmb                                 in  g.rexp.q.ext_add.findall(param):                        #case 2020.05.21
                bsq_ext_add                                 +=  "r19:"  +   ext_main_nmb                        + " || "# отбор по разделению дополнительных данных.#case 2020.05.21
            # получаю количество событий ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for amount                                      in g.rexp.q.amount_re.findall(param):
                bsq_amount                                  =   re.sub(r'\s',"",amount)
        # дополнительные установки ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if bsq_date_start                                   ==  "":                                                     # если без отбора по налачу
            bsq_date_start                                  =   "*"                                                     # то *
        if bsq_date_end                                     ==  "":                                                     # если без отбора по концу
            bsq_date_end                                    =   "*"                                                     # то *
        # строю запрос ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        bsq_dates                                           =   "(r1:[" + bsq_date_start + " TO " + bsq_date_end + "])" # формирую отбор по датам
        #ret_query                                           =   g.execution.solr.url_main + "/" + ib_name + "/select?q="# начало строки поискового запроса
        ret_query                                           =   bsq_dates                                               # r1 добавляю в запрос отбор по датам
        ret_query                                           +=  reader.q_prep("AND" ,bsq_status_trans)                  # r2 добавляю в запрос отбор по статусам транзакции
        ret_query                                           +=  reader.q_prep("AND" ,bsq_users)                         # r4 добавляю в запрос отбор по пользователям
        ret_query                                           +=  reader.q_prep("AND" ,bsq_computers)                     # r5 добавляю в запрос отбор по компьютерам
        ret_query                                           +=  reader.q_prep("AND", bsq_applications)                  # r6 добавляю в запрос отбор по компьютерам
        ret_query                                           +=  reader.q_prep("AND" ,bsq_actions)                       # r8 добавляю в запрос отбор по событиям
        ret_query                                           +=  reader.q_prep("AND" ,bsq_levels)                        # r9 уровень важности
        ret_query                                           +=  reader.q_prep("AND", bsq_comments)                      # r10 добавляю в запрос отбор по комментариям
        ret_query                                           +=  reader.q_prep("AND", bsq_metadatas)                     # r11 добавляю в запрос отбор по метаданным
        ret_query                                           +=  reader.q_prep("AND", bsq_datas)                         # r12 добавляю в запрос отбор по данным
        ret_query                                           +=  reader.q_prep("AND", bsq_data_presentations)            # r13 добавляю в запрос отбор по представлению данных
        ret_query                                           +=  reader.q_prep("AND", bsq_servers)                       # r14 добавляю в запрос отбор по серверам
        ret_query                                           +=  reader.q_prep("AND", bsq_main_ports)                    # r15 добавляю в запрос отбор по основным портам
        ret_query                                           +=  reader.q_prep("AND", bsq_add_ports)                     # r16 добавляю в запрос отбор по дополнительным портам
        ret_query                                           +=  reader.q_prep("AND", bsq_seanses)                       # r17 добавляю в запрос отбор по сеансам
        ret_query                                           +=  reader.q_prep("AND", bsq_ext_main)                      # r18(21) добавляю в запрос отбор по разделению основных данных
        ret_query                                           +=  reader.q_prep("AND", bsq_ext_add)                       # r19(22) добавляю в запрос отбор по разделению вспомогательных данных
        post_query                                          =   {}
        post_query["query"]                                 =   ret_query
        post_query["params"]                                =   {}
        post_query["params"]["sort"]                        =   "r1 desc, r1nmb desc"
        post_query["params"]["rows"]                        =   bsq_amount
        #ret_query                                           +=  "&rows="+ bsq_amount                                    # добавляю в запрос количество для отбора
        #ret_query                                           +=  "&sort=r1 desc, r1nmb desc"                             # добавляю в запрос сортировку
        return post_query
    # ------------------------------------------------------------------------------------------------------------------
    # служебная функция - убирает последние || и всё после них до конца строки и укутывает в скобки
    # ------------------------------------------------------------------------------------------------------------------
    def q_prep(str1,str2):
        if(str2):
            qp_sorted                                       =   []
            for each in str2.split(' || '):                                                                             # хочу отсортировать перед использованием, но только для цифр )))
                if len(each)                                >   3:
                    qp_dec                                  =   re.findall(r'(r\d+)\:(.*)',each)[0]
                    if(qp_dec[1].isdigit()):                                                                            # всё-таки делаю это только для цифр )))
                        num                                 =   "0" + qp_dec[1] if len(qp_dec[1]) ==  1 else qp_dec[1]
                    else:
                        num                                 =   qp_dec[1]
                    if qp_dec[1].find(":")                  >   0:                                                      # если в строке есть двоеточие, то её надо экранировать
                        qp_sorted.append(qp_dec[0] + ':"' + num + '"')
                    else:
                        qp_sorted.append(qp_dec[0] + ':' + num)
            qp_sorted.sort()
            str2                                            =   ""
            for each in qp_sorted:
                str2                                        +=  each + ' || '
            return str1+ " ("+re.sub(r'\|\|[^\|]*$','',str2)+")"
        else:
            return ""
    # ------------------------------------------------------------------------------------------------------------------
    # функция конвертации даты из внутреннего формата 1С в человеческий
    # ------------------------------------------------------------------------------------------------------------------
    def hex_1c_time_to_human_string(c1hts):
        if int(c1hts,16)                                    ==  0:
            return "0"
        # подготовка исходных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Ndt                                                 =   reader.int_1c_time_to_obj(int(int(c1hts,16)))
        # формирую строку результата ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        result                                              =   Ndt[2] + "." + Ndt[1] + "." + Ndt[0] + " " + \
                                                                Ndt[3] + ":" + Ndt[4] + ":" + Ndt[5]
        return result
    # ------------------------------------------------------------------------------------------------------------------
    # функция конвертации даты из внутреннего формата в 1С
    # ------------------------------------------------------------------------------------------------------------------
    def int_1c_time_to_human_string(c1hts,islgd):
        if int(c1hts)                                       ==  0:
            return "0"
        # подготовка исходных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Ndt                                                 =   reader.int_1c_time_to_obj(int(c1hts),islgd)
        # формирую строку результата ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        result                                              =   Ndt[2] + "." + Ndt[1] + "." + Ndt[0] + " " + \
                                                                Ndt[3] + ":" + Ndt[4] + ":" + Ndt[5]
        return result
    # ------------------------------------------------------------------------------------------------------------------
    # функция конвертации даты из внутреннего формата 1С в человеческий
    # ------------------------------------------------------------------------------------------------------------------
    def int_1c_time_to_old_zhr_time(c1hts,islgd):
        # подготовка исходных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Ndt                                                 =   reader.int_1c_time_to_obj(c1hts,islgd)
        result                                              =   str(Ndt[0]) + \
                                                                str(Ndt[1]) + \
                                                                str(Ndt[2]) + \
                                                                str(Ndt[3]) + \
                                                                str(Ndt[4]) + \
                                                                str(Ndt[5])
        return result
    # ------------------------------------------------------------------------------------------------------------------
    # функция конвертации даты из внутреннего формата 1С в человеческий, спасибо Серёже за простоту
    # ------------------------------------------------------------------------------------------------------------------
    def int_1c_time_to_obj(c1hts,islgd=False):
        val                                                 =   int(c1hts / 10000) - 62136244800
        if islgd:
            val                                             +=  int(int(t.get_time_zone()) * 60 * 60)                   # смещение на сервере для нового формата в секундах
        dt                                                  =   datetime.datetime.fromtimestamp(val)
        Ndt                                                 =   []
        Ndt.append( str(dt.year)                                                    )
        Ndt.append( str(dt.month)   if  dt.month  > 9   else "0" + str(dt.month)    )
        Ndt.append( str(dt.day)     if  dt.day    > 9   else "0" + str(dt.day)      )
        Ndt.append( str(dt.hour)    if  dt.hour   > 9   else "0" + str(dt.hour)     )
        Ndt.append( str(dt.minute)  if  dt.minute > 9   else "0" + str(dt.minute)   )
        Ndt.append( str(dt.second)  if  dt.second > 9   else "0" + str(dt.second)   )
        return Ndt
    # ------------------------------------------------------------------------------------------------------------------
    # вот это я упорото декодировал руками. Пусть останется для истории как пример усердия и непродуманности решения
    # ------------------------------------------------------------------------------------------------------------------
    def int_1c_time_to_obj_old(c1hts,islgd=False):
        # подготовка исходных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        lgd_add                                             =   int(int(t.get_time_zone()) * 60)                        # смещение на сервере для нового формата
        NJulGrigOffset                                      =   15 * 24 * 60 * 60                                       # типа 14 дней какого-то смещения
        c1hts_int                                           =   c1hts/10000+NJulGrigOffset                              # перевожу в секунда
        c1hts_int                                           =   c1hts_int+lgd_add if islgd else c1hts_int               # на новом формате другие значения смещения???????!!!!!!!!!!!!!!!
        Ndt                                                 =   [1, 1, 1, 0, 0, 0]
        Nyear                                               =   [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]        # распределение количества дней по месяцам года в обычном году
        Nyear_leap                                          =   [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]        # распределение количества дней по месяцам года в високосном году
        Nyear_sec                                           =   365 * 24 * 60 * 60                                      # секунд в обычном году
        Nyear_leap_sec                                      =   366 * 24 * 60 * 60                                      # секунд в високосном году
        Nleap_divider                                       =   4                                                       # каждый Nleap_divider год - высокосный
        Nleap                                               =   (Ndt[0] % Nleap_divider) == 0                           # признак високосности первого года
        NsecDay                                             =   60 * 60 * 24                                            # секунд в дне
        NSecHour                                            =   60 * 60                                                 # секунд в часе
        NSecMin                                             =   60                                                      # секунда в минуте
        NyrSec                                              =   Nyear_leap_sec if Nleap else Nyear_sec                  # выбираем количество секудна для первого года
        # вычисляю год ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while (c1hts_int - NyrSec)                          >   0:
            Ndt[0]                                          +=  1                                                       # увеличиваю массив из дат на один год
            c1hts_int                                       -=  NyrSec                                                  # а количество секунд года - вычитаю
            Nleap                                           =   (Ndt[0] % Nleap_divider) == 0                           # рассчитываю призна високосности следюущего года
            NyrSec                                          =   Nyear_leap_sec if Nleap else Nyear_sec                  # и, если надо, меняю количество секунд для следующего года
        # вычисляю месяц ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Nyr                                                 =   Nyear_leap if Nleap else Nyear                          # количество месяцев для этого года, високосный он или нет
        Nstop                                               =   False
        while not Nstop:                                                                                                # обошёлся здесь без итератора. порядковый номер месяца и есть итератор
            if Ndt[1]                                       <   12:                                                     # это потому, что 13 месяца у меня нет
                if (abs(c1hts_int) - Nyr[Ndt[1]] * NsecDay) < 0:
                    Nstop = True
                else:
                    c1hts_int                               -=  Nyr[Ndt[1]] * NsecDay                                   # уменьшаю количество секунду на количество секунд этого месяца
                    Ndt[1]                                  +=  1                                                       # увеличиваю месяц
            if Ndt[1]                                       ==  12:                                                     # а в чикле обработки 12-го до него доходило
                Nstop                                       =   True
        # вычисляю день ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while (c1hts_int - NsecDay)                         >   0:
            Ndt[2]                                          +=  1
            c1hts_int                                       -=  NsecDay
        # вычисляю час ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while (c1hts_int - NSecHour)                        >   0:
            Ndt[3]                                          +=  1
            c1hts_int                                       -=  NSecHour
        # вычисляю минуту ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while (c1hts_int - NSecMin)                         >   0:
            Ndt[4]                                          +=  1
            c1hts_int                                       -=  NSecMin
        # формирую строку результата ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Ndt[5]                                              =   int(c1hts_int)

        Ndt[0]                                              =   str(Ndt[0])
        Ndt[1]                                              =   str(Ndt[1]) if Ndt[1] > 9 else "0" + str(Ndt[1])
        Ndt[2]                                              =   str(Ndt[2]) if Ndt[2] > 9 else "0" + str(Ndt[2])
        Ndt[3]                                              =   str(Ndt[3]) if Ndt[3] > 9 else "0" + str(Ndt[3])
        Ndt[4]                                              =   str(Ndt[4]) if Ndt[4] > 9 else "0" + str(Ndt[4])
        Ndt[5]                                              =   str(Ndt[5]) if Ndt[5] > 9 else "0" + str(Ndt[5])
        return Ndt
    # ------------------------------------------------------------------------------------------------------------------
    # усердное декодирование строки для SQLite записей с нормальной обработкой проблемной буквы И
    # ------------------------------------------------------------------------------------------------------------------
    def force_decode(string):
        ret                                                 =   ""
        if not len(string) > 0:
            return ret
        not_converted                                       =   True
        while not_converted:
            try:
                ret                                         =   string.encode('cp1251').decode('utf8')                  # пытаемся декодировать
                not_converted                               =   False
            except Exception as e:                                                                                      # и если не вышло
                pos                                         =   re.findall(r'position (\d+)',str(e))
                if(len(pos)                                 >   0):
                    pos                                     =   int(pos[0])
                    bad                                     =   string[pos:pos+1]                                       # то определяем, где не вышло
                    if bad.encode('utf8')                   ==  b'\xc2\x98':                                            # и если это буква И
                         ret                                =   reader.force_decode(string[:pos-1]) \
                                                            +   'И' \
                                                            +   reader.force_decode(string[pos+1:])                     # то декодируем куски без неё (рекуррсивно, естественно)
                    else:                                                                                               # А если не она
                        ret                                 =   reader.force_decode(string[:pos-1]) \
                                                            +   reader.force_decode(string[pos+1:])                     # то вообще без этого символа
                    not_converted                           =   False
                else:
                    ret                                     =   str(e)
                    not_converted                           =   False
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # проверяем, ялвляется ли ЖР ИБ словарём нового формата
    # ------------------------------------------------------------------------------------------------------------------
    def is_ib_is_lgd(iiil):
        ret                                                 =   False
        for ib                                              in  g.parser.ibases:
            if ib.get('ibase_name')                         ==  iiil:
                ret                                         =   ib.get('ibase_jr_format') ==  'lgd'
        return ret
    #-------------------------------------------------------------------------------------------------------------------
    # возвращаю количество данных для базы
    # -------------------------------------------------------------------------------------------------------------------
    def get_total_size(base):
        for each in g.parser.ibases:
            if each[g.nms.ib.name]                          ==  base:
                return each[g.nms.ib.total_size]
    #-------------------------------------------------------------------------------------------------------------------
    # возвращаю количество распарсенных данных для базы
    # -------------------------------------------------------------------------------------------------------------------
    def get_parsed_size(base):
        for each in g.parser.ibases:
            if each[g.nms.ib.name]                          ==  base:
                return each[g.nms.ib.parsed_size]
