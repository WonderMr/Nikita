# -*- coding: utf-8 -*-
import sys
import  threading
import  os
import  time
import  operator
import  requests
import  json
from    dotenv              import load_dotenv 
load_dotenv() 
# ======================================================================================================================
from    src.tools           import  tools                   as  t
from    src                 import  globals                 as  g
from    src.dictionaries    import  dictionary              as  d
from    src                 import  reader                  as  r
from    clickhouse_driver   import  Client                  as  ch
from    datetime            import  datetime
import  src.messenger                                       as  m
# ======================================================================================================================
# класс, умеющий разбирать записи ЖР 1с и отправлять их в Solr
# ======================================================================================================================
class parser(threading.Thread):
    json_data                                               =   {}                                                      # для хранения записей json внутри класса
    file_list_updater                                       =   None
    stopMe                                                  =   False
    chclient                                                =   None
    # ------------------------------------------------------------------------------------------------------------------
    # инициализация класса и создание дочернего потока filelistupdater'а
    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name + " parser"
        self.json_data[self.name]                           =   []
        self.files_list_updater                             =   self.files_list_updater_thread_class("list " + name)    # создаём поток в зависиомсти от вызываемого
        self.files_list_updater.start()
        self.stopMe                                         =   False
        self.chclient                                       =   ch(host=os.getenv("CLICKHOUSE_HOST"), user=os.getenv("CLICKHOUSE_USER"), password=os.getenv("CLICKHOUSE_PASSWORD"))
        self.chclient.execute('SELECT 1')
        t.debug_print("Thread initialized", self.name)
    # ------------------------------------------------------------------------------------------------------------------
    # Запуск и работа класса
    # ------------------------------------------------------------------------------------------------------------------
    def run(self):
        while True and not self.stopMe:
            list                                            =   self.files_list_updater.ibases_files                    # сокращаем
            try:
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                while (g.parser.ibases)                     ==  None:                                                   # ждём инициализации
                    time.sleep(g.waits.in_cycle_we_trust)
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                if(len(list)                                >   0):                                                     # если есть над чем работать
                    self.parse_file(list[0][1] + list[0][2],list[0][0])                                                 # обрабатываем очередной файл
                    del list[0]                                                                                         # и убираем из очереди
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                time.sleep(g.waits.in_cycle_we_trust)
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            except Exception as e:
                t.debug_print("Exception6 "+str(e),self.name)
    # ------------------------------------------------------------------------------------------------------------------
    # Остановка класса
    # ------------------------------------------------------------------------------------------------------------------
    def stop(self):
        #self.file_list_updater.stop()                                                                                   # останавливаю поток субкласса обновления файлов
        self.stopMe                                         =   True
    # ------------------------------------------------------------------------------------------------------------------
    # вложенный класс/поток для обновления имен файлов - это происходит асинхронно
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    class files_list_updater_thread_class(threading.Thread):
        ibases_files                                        =   []                                                      # список обрабатываемых файлов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def __init__(self, name):
            threading.Thread.__init__(self)
            self.name                                       =   name
            t.debug_print("Thread initialized", self.name)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def run(self):                                                                                                  # обновляет глобальный список обрабатываемых файлов
            if (self.name.upper()).find('LGP')              >   0:                                                      # если старый формат ЖР
                regexp                                      =   g.rexp.is_lgP_file_re                                   # если старый формат ЖР
            if (self.name.upper()).find('LGD')              >   0:                                                      # если новый формат ЖР
                regexp                                      =   g.rexp.is_lgD_file_re                                   # если новый формат ЖР
            while True:
                g.parser.ibases_lpf_files                   =   []
                local_list                                  =   []
                for ibase in g.parser.ibases:                                                                           # по всем базам
                    total_files_or_recs_size                =   0
                    total_parsed                            =   0
                    files                                   =   [
                                                                    element for element
                                                                    in os.listdir(ibase[g.nms.ib.jr_dir])
                                                                    if os.path.isfile(os.path.join(ibase[g.nms.ib.jr_dir], element))
                                                                    and regexp.findall(element)
                                                                ]                                                       # получаю список всех файлов ЖР базы
                    for file in files:                                                                                  # по всем файлам
                        try:
                            full_name                       =   os.path.join(ibase[g.nms.ib.jr_dir], file)
                            # для старого формата - размер файла ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            if (file.upper()).find('.LGP')  >   0:                                                      # если формат старый
                                this_file_size              =   os.stat(full_name).st_size
                            # для нового - количество записей ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            if (file.upper()).find('.LGD')  >   0:                                                      # если формат новый
                                (max_row, min_row)          =   t.get_lgd_evens_count(full_name)
                                this_file_size              =   max_row + 1 - min_row
                            # прибавляю к общему для базы ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            total_files_or_recs_size        +=  this_file_size
                            # добавляю файлы в списко для обработки только размер отличается ~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            get_saved_size                  =   parser.read_file_state(
                                                                        full_name,
                                                                        this_file_size
                                                                    )
                            if this_file_size               !=  get_saved_size:
                                ibase_file                  =   [
                                                                        ibase[g.nms.ib.name],
                                                                        ibase[g.nms.ib.jr_dir] + "/",
                                                                        file
                                                                ]                                                       # и кладу в общий массив с информацией о базе
                                local_list.append(ibase_file)
                            # общее для всех~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            total_parsed                    +=  get_saved_size
                        except Exception as e:
                            t.debug_print(str(e),self.name)
                        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # обнуляю размер распарсенных файлов ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    if files:                                                                                           # для многопоточности
                        ibase[g.nms.ib.parsed_size]         =   total_parsed                                            # устанавливаю актуальный размер распарсенного для базы
                        ibase[g.nms.ib.total_size]          =   total_files_or_recs_size                                # устанавливаю актуальный размер базы
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                if local_list:                                                                                          # для многопоточности
                    local_list.sort(key=operator.itemgetter(2), reverse=True)                                           # сортирую по убыванию
                    self.ibases_files                       =   local_list                                              # чтобы сразу готовый результат был
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Безусловное ожидание для https://github.com/WonderMr/Journal2Ct/issues/48
                time.sleep(g.waits.parser_sleep_on_update_filelist)
    # ------------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------------
    # добавление в parser.json_data данных из разобранной записи
    # ------------------------------------------------------------------------------------------------------------------
    def add_to_json_data(self, fj_rec, fj_dt_sort_add, fj_id, fj_pos, fj_size, fj_base):                                # первый параметр - распарсенные поля записи ЖР
        try:
            if(g.debug.on_parser):
                t.debug_print("adding to json "+str(fj_rec),self.name)
            local_json                                      =   {}                                                      # второй - порядок времени для сортировки одинаковых моментов
            cc                                              =   1 
            local_json['id']                                =   t.get_file_id_by_name(fj_id)                            # третий - имя файла
            local_json['pos']                               =   fj_pos                                                  # четвёртый - смещение
            local_json['len']                               =   fj_size                                                 # пятый - размер записи
            local_json['r1']                                =   fj_rec[0]
            local_json['r1nmb']                             =   fj_dt_sort_add
            local_json['r2']                                =   fj_rec[1]
            local_json['r3h']                               =   "0x" + fj_rec[2]
            local_json['r3']                                =   int(int(fj_rec[2],16)/10000)                            # в десятичном формате
            cc = 2
            local_json['r3ah']                              =   "0x" + fj_rec[3]
            cc = 3
            local_json['r3a']                               =   int(fj_rec[3],16)
            cc = 4
            local_json['rr4']                               =   g.execution.c1_dicts.users[fj_base][fj_rec[4]] if int(fj_rec[4])>0\
                                                                else {"uuid":"","name":""}
            cc = 5
            local_json['rr5']                               =   g.execution.c1_dicts.computers[fj_base][fj_rec[5]] if int(fj_rec[5])>0\
                                                                else "0"
            cc = 6
            local_json['rr6']                               =   g.execution.c1_dicts.applications[fj_base][fj_rec[6]]
            cc = 7
            local_json['rr7']                               =   fj_rec[7]
            cc = 8
            local_json['rr8']                               =   g.execution.c1_dicts.actions[fj_base][fj_rec[8]]
            cc = 9
            local_json['rr9']                               =   fj_rec[9]
            cc = 10
            local_json['rr10']                              =   fj_rec[10].replace("'","''").replace('\\','\\\\')
            cc = 11
            local_json['rr11']                              =   g.execution.c1_dicts.metadata[fj_base][fj_rec[11]] if not fj_rec[11]=="0"\
                                                                else {"uuid":"", "name":""}
            cc = 12
            local_json['rr12']                              =   fj_rec[12].replace("'","''").replace('\\','\\\\')
            cc = 13
            local_json['rr13']                              =   fj_rec[13].replace("'","''").replace('\\','\\\\')
            cc = 14
            local_json['rr14']                              =   g.execution.c1_dicts.servers[fj_base][fj_rec[14]] if int(fj_rec[14])>0\
                                                                else ""
            cc = 15
            local_json['rr15']                              =   g.execution.c1_dicts.ports_main[fj_base][fj_rec[15]] if int(fj_rec[15])>0\
                                                                else "0"
            cc = 16
            local_json['rr16']                              =   g.execution.c1_dicts.ports_add[fj_base][fj_rec[16]] if int(fj_rec[16])>0\
                                                                else '0'
            cc = 17
            local_json['rr17']                              =   fj_rec[17]
            for l_i in range (4,18):
                local_json['r'+str(l_i)]                    =   fj_rec[l_i]
            if len(fj_rec) - 1                              >   g.rexp.sel_re_ext_nmb:
                local_json['r18']                           =   d.get_main_area(fj_base, fj_rec[22], fj_rec[23])        # case 2020.05.21
                local_json['rr18']                          =   local_json['r18']
                local_json['r19']                           =   d.get_add_area(fj_base, fj_rec[20], fj_rec[21])         # case 2020.05.21
                local_json['rr19']                          =   local_json['r19']
            else:
                local_json['r18']                           =   '0'                                                     # case 2020.05.21
                local_json['rr18']                          =   '0'
                local_json['r19']                           =   '0'                                                     # case 2020.05.21
                local_json['rr19']                          =   '0'
            self.json_data[self.name].append(local_json)
            if(g.debug.on_parser):
                t.debug_print(json.dumps(local_json, indent=2), self.name)
        except Exception as e:
            t.debug_print(f"Exception while add_to_json {str(e)}", self.name)
            t.seppuku(111)
            return False
        return True
    # ------------------------------------------------------------------------------------------------------------------
    # отправка post запроса
    # ------------------------------------------------------------------------------------------------------------------
    def post_query(self, url, data, base_name):
        ret_ok                                              =   200
        ret_err                                             =   500
        try:
            #t.debug_print("post to "+url,g.threads.parser.name)
            t.debug_print("posting to ClickHouse", g.threads.parser.name)
            #ret                                             =   requests.post(url=url,json=data).status_code
            #rec                                             =   [0]
            querystring                                     =   ""
            querystring19                                   =  f"insert into zhr1c.`{base_name}`(r1,r1a,r2,r3,r3a,r4name,r4guid,r5,r6,r7,r8,r9,r10,r11uuid,r11name,r12,r13,r14,r15,r16,r17,r18,r19) values ("
            #querystring9                                   =  "insert into nikita.test9(r1,r2,r3,r3a,r4name,r4guid,r5,r6,r7,r8,r9,r10,r11name,r11guid,r12,r13,r14,r15,r16,r17,r18,r19) values ("
            post_count                                      =   0
            rec_no                                          =   0
            for rec in data:
                post_count                                  +=  1
                rec_no                                      +=  1
                #t.debug_print("iter rec "+str(rec_no), g.threads.parser.name)
                date                                        =   f"{rec['r1'][0:4]}-{rec['r1'][4:6]}-{rec['r1'][6:8]} {rec['r1'][8:10]}:{rec['r1'][10:12]}:{rec['r1'][12:14]}"
                ts                                          =   int(datetime.fromisoformat(date).timestamp())
                tsstr                                       =   str(ts)
                querystring                                 +=  f"{tsstr},"                         #r1 is datetime, converted to int
                querystring                                 +=  f"toDateTime('{datetime.utcfromtimestamp(ts)}'),"#r1a is datetime
                querystring                                 +=  f"'{rec['r2']}',"                   #r2 is one char
                querystring                                 +=  f"{rec['r3h']},"                    #r3h is string of hex
                querystring                                 +=  f"{rec['r3ah']},"                   #r3ah is string of hex
                querystring                                 +=  f"'{rec['rr4']['name']}',"
                querystring                                 +=  f"'{rec['rr4']['uuid']}',"
                for l_i in range(5, 7):
                    querystring                             +=  f"'{rec['rr' +str(l_i)]}',"         #r5-r6 is strings
                querystring                                 +=  f"{rec['rr7']},"                    #r7 номер соединения
                for l_i in range(8, 11):
                    querystring                             +=  f"'{rec['rr' +str(l_i)]}',"         #r8-r12 is strings
                querystring                             +=  f"'{rec['rr11']['uuid']}',"         #r11
                querystring                             +=  f"'{rec['rr11']['name']}',"         #r11
                for l_i in range(12, 15):
                    querystring                             +=  f"'{str(rec['rr'+str(l_i)])}',"
                for l_i in range(15, 20):
                    querystring                             +=  f"{rec['rr'+str(l_i)]},"
                querystring                                 =   querystring[:-1]+"),("
                if post_count >= g.parser.maxrecsize: # or len(querystring) > 100000:
                    if (g.debug.on_parser):
                        t.debug_print("data will be posted", self.name)
                        t.debug_print(querystring)
                    t.debug_print(f"Posting {str(post_count)} records"  , g.threads.parser.name)
                    t.debug_print(f"Block size: {str(len(querystring))}", g.threads.parser.name)
                    querystring                             =   querystring[:-3] + ")"
                    self.chclient.execute(querystring19 + querystring)
                    post_count                              =   0
                    querystring                             =   ""
            if post_count > 0: # send the rest
                if (g.debug.on_parser):
                    t.debug_print("data will be posted", self.name)
                    t.debug_print(querystring)
                t.debug_print(f"Posting {str(post_count)} rest records"  , g.threads.parser.name)
                t.debug_print(f"Block size: {str(len(querystring))}", g.threads.parser.name)
                querystring                                 =   querystring[:-3] + ")"
                self.chclient.execute(querystring19 + querystring)
            #self.chclient.execute(querystring9+querystring)
            #self.json_data[self.name]                       =   []
        except Exception as e:
            #for ibase in g.parser.ibases:
            #    self.check_base_exists(ibase[g.nms.ib.name])
            t.debug_print("Exception 9 " + str(e))
            return ret_err
        return ret_ok
    # ------------------------------------------------------------------------------------------------------------------
    # отправка get запроса
    # ------------------------------------------------------------------------------------------------------------------
    def get_query(self, url):
        ret                                                 =   0
        try:
            #t.debug_print("post to "+url,g.threads.parser.name)
            ret                                             =   requests.get(url=url).status_code
        except Exception as e:
            t.debug_print(f"Exception 10 {str(e)}")
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # отправка parser.json_data в solr и commit. До победного
    # ------------------------------------------------------------------------------------------------------------------
    def solr_post_json_data(self, spjd_base):
        start_time                                          =   time.time()
        spjd_sended                                         =   False
        while not spjd_sended:
            try:
                #while not g.execution.solr.started:                                                                     # ждём, пока Solr проснётся
                #    t.debug_print("waiting for solr to start",self.name)
                #    time.sleep(g.waits.solr_wait_start)
                t.debug_print("Posting", self.name)
                # первый запрос ----------------------------------------------------------------------------------------
                spjd_post_url                               =   f"{g.execution.solr.url_main}/{spjd_base}/update?wt=json"
                spjd_ret_code                               =   self.post_query(
                                                                    spjd_post_url,
                                                                    data      = self.json_data[self.name],
                                                                    base_name = spjd_base
                                                                )
                # шлём, пока не пройдёт --------------------------------------------------------------------------------
                while spjd_ret_code                         !=  200:                                                    # http://localhost:8983/solr/PER/update?wt=json
                    t.debug_print(f"Post data returned {str(spjd_ret_code)}, retrying")
                    time.sleep(g.waits.solr_on_bad_send_to)
                    spjd_ret_code                           =   self.post_query(
                                                                    spjd_post_url,
                                                                    data    =   self.json_data[self.name]
                                                                )
                t.debug_print("Post data was sucesfully sended", self.name)
                del self.json_data[self.name][:]                                                                        # пачку отправили, обнуляем данные
                # попытка коммита --------------------------------------------------------------------------------------
                # spjd_commit_url                             =   g.execution.solr.url_main +  "/" \
                #                                            +   spjd_base + "/update?commit=true&waitSearcher=false"
                # spjd_ret_code                               =   self.get_query(spjd_commit_url)
                # пока всё не зайдёт

                spjd_ret_code                               =   200
                while spjd_ret_code                         !=  200:
                    t.debug_print(f"Post commit returned {str(spjd_ret_code)}, retrying")
                    time.sleep(g.waits.solr_on_bad_send_to)
                    #spjd_ret_code                           =   self.get_query(spjd_commit_url)
                t.debug_print("Commit was succefully sended", self.name)
                spjd_sended                                 =   True
            except Exception as ee:
                error_message                               = f"Ошибка при отправке в SOLR: {str(ee)}"
                t.debug_print(error_message, self.name)
                time.sleep(g.waits.solr_on_bad_send_to)
        t.debug_print("Post took "+str(time.time()-start_time),self.name)
    # ------------------------------------------------------------------------------------------------------------------
    # проверка корректности записи через её чтение и разбор
    # ------------------------------------------------------------------------------------------------------------------
    def check_rec(cr_name,cr_pos,cr_len):
        f                                                   =   open(cr_name, 'rb')
        f.seek(cr_pos)
        data                                                =   f.read(cr_len).decode(encoding='UTF8')
        f.close()
        if g.rexp.my_re.match(data):
            return True
        else:
            t.debug_print('invalid record '+data)
            return False
    # ------------------------------------------------------------------------------------------------------------------
    # разбор и индексирование одного файла
    # ------------------------------------------------------------------------------------------------------------------
    def parse_file(self, pf_name, pf_base):                                                                             # обработка файла
        try:
            #self.chclient.execute("CREATE TABLE IF NOT EXISTS nikita.`" + pf_base + "`(r1  DateTime CODEC(ZSTD(14)),r2  FixedString(1), r3  Int64, r3a Int64, r4name  String CODEC(ZSTD(14)), r4guid  String CODEC(ZSTD(14)), r5  String CODEC(ZSTD(14)), r6  String CODEC(ZSTD(14)), r7  String CODEC(ZSTD(14)), r8  String CODEC(ZSTD(14)), r9  FixedString(1), r10 String CODEC(ZSTD(14)), r11name String CODEC(ZSTD(14)), r11guid String CODEC(ZSTD(14)), r12 String CODEC(ZSTD(14)), r13 String CODEC(ZSTD(14)), r14 String CODEC(ZSTD(14)), r15 Int32, r16 Int32, r17 Int64, r18 Int32, r19 Int32 ) ENGINE = Log()")
            if g.rexp.is_lgD_file_re.findall(pf_name):
                self.parse_lgd_file(pf_name, pf_base)                                                                    # обрабатываю новый формат ЖР
            if g.rexp.is_lgP_file_re.findall(pf_name):                                                                  # или старый формат ЖР
                self.parse_lgp_file(pf_name, pf_base)
        except Exception as e:
            t.debug_print("got parsefile exception on "+pf_base+" - "+pf_name+". Error is:"+str(e))
            sys.exit(-1)
    # ------------------------------------------------------------------------------------------------------------------
    # разбор и индексирование одного файла нового формата
    # ------------------------------------------------------------------------------------------------------------------
    def parse_lgd_file(self,pf_name,pf_base):                                                                           # обработка файла старого формата
        file_state                                          =   {}
        # Проверка наличия файла ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if not os.path.exists(pf_name):
            t.debug_print("file not found "+pf_name,self.name)
            return
        # Готовлюсь к чтению ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            # получаем текущий статус парсинга ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            (max_row,min_row)                               =   t.get_lgd_evens_count(pf_name)
            pf_size                                         =   max_row+1-min_row
            if(pf_size == 1):
                t.debug_print(pf_base + " has empty zhr.", self.name)
                return
            else:
                t.debug_print(pf_base+":pf_size = " + str(pf_size), self.name)
            file_state['filename']                          =   pf_name                                                 # локальная структура json с именем файла
            file_state['filesize']                          =   pf_size                                                 # локальная структура json с размером файла
            file_state['filesizeread']                      =   parser.read_file_state(pf_name,file_state['filesize'])  # пытаюсь получить размер прочитанных байт из сохранённого состояния
            # сообщим о начале обработки, при необходимости~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if int(file_state['filesizeread'])              <   int(file_state['filesize']):
                t.debug_print(pf_base+":processing " + pf_base + "@" + pf_name, self.name)
            # разбираем файл, при необходимости~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            while int(file_state['filesizeread'])           <   int(file_state['filesize']):                            # пока количеством не дошёл до конца
                plf_rowID                                   =   file_state['filesizeread'] + min_row - 1                # у нас же смещение может быть в обрезанных файлах!!!
                limit_delta                                 =   int(file_state['filesize'])\
                                                            -   int(file_state['filesizeread'])                         # https://github.com/WonderMr/Journal2Ct/issues/40
                limit_records                               =   g.parser.lgd_parse_records_limit \
                                                                if limit_delta>g.parser.lgd_parse_records_limit \
                                                                else limit_delta                                        # читаю не больше, чем то количество, о котором знаю
                t.debug_print(pf_base + ":plf_rowID = " + str(plf_rowID), self.name)
                plf_query                                   =   '''
                                                                  select 
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
                                                                    session,                                                                    
                                                                    rowID 
                                                                    from EventLog where rowID > '''         + \
                                                                        str(plf_rowID)                      + \
                                                                " ORDER BY rowID ASC LIMIT "+str(limit_records)
                if g.debug.on_parser:
                    t.debug_print(pf_base+ ":run Query \n"+plf_query ,self.name)
                ret                                         =   t.sqlite3_exec(pf_name, plf_query)
                if ret:
                    result                                  =   []
                    rslt                                    =   {}
                    prev_date                               =   ""
                    r1_nmb                                  =   0
                    for rec                                 in ret:
                        rslt[0]                             =   r.reader.int_1c_time_to_old_zhr_time(rec[0],islgd=True) # Дата
                        if rslt[0]                          ==  prev_date:                                              # здесь трюк с сортировкой дат с одинаковым временем
                            r1_nmb                          +=  1
                        else:
                            r1_nmb                          =   0
                        prev_date                           =   rslt[0]
                        rslt[1]                             =   d.trans_state.get(str(rec[1]))                          # Статус Транзакции
                        rslt[2]                             =   hex(rec[2])                                             # дата и время транзхакции в десятичном представлени
                        rslt[3]                             =   hex(rec[3])                                             # ID Тразакции
                        for l_i in range (4,9):
                            rslt[l_i]                       =   rec[l_i]                                                # 4 - Код пользователя # 5 - Код компьютера # 6 - код приложения # 7 - номер соединения # 8 - номер события
                        rslt[9]                             =   d.severity.get(str(rec[9]))                             # 9 - Severity - Важность
                        rslt[10]                            =   rec[10]                                                 # 10- комментарий
                        rslt[11]                            =   rec[11] if str(rec[11]).isdigit() else 0                # 11- номер метаданных
                        rslt[12]                            =   r.reader.force_decode(rec[12])                          # 12- данные - надо привести в нормальный формат
                        for l_i in range (13,18):
                            self.i_ = rec[l_i]
                            rslt[l_i]                       = self.i_  # 13- представление данных # 14- номер сервера # 15- номер порта #16- номер доп порта #17- сеанс
                        r18_nmb                             =   rec[18]                                                 # сохраняю значение row_id #case 2020.05.21
                        rslt[18]                            =   '0'                                                     # заглушка #case 2020.05.21
                        rslt[19]                            =   '0'                                                     # заглушка #case 2020.05.21
                        result.append(rslt)
                        m.check_event(result[0],pf_base)
                        if not self.add_to_json_data(
                                                            result[0],
                                                            r1_nmb,
                                                            pf_name,
                                                            r18_nmb,
                                                            0,
                                                            pf_base
                                                    ):                                                                  # добавляю в json структуры, нумератор записей с одинаковой датой, имя файла, rowID записи и "" как размер #case 2020.05.21
                            t.debug_print("Exception : не удалось обработать запись " + str(result))
                        del result[:]
                    # отправили тысячу записей или все оставшиемся, высылаем в SOLR~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    t.debug_print(pf_base+ ":commiting with state: \n"  +
                                  "total length     = "     +   str(file_state['filesize'])     + "\n" +
                                  "new curr.length  = "     +   str(
                                                                    file_state['filesizeread']  +
                                                                    len(self.json_data[self.name])
                                                                )                               + "\n" +
                                  "current length   = "     +   str(file_state['filesizeread']) + "\n" +
                                  "commited records = "     +   str(
                                                                    len(self.json_data[self.name])),
                                                                    self.name
                                                                )                                                       # add 2019.02.15 для https://github.com/WonderMr/Journal2Ct/issues/40
                    file_state['filesizeread']              =   int(file_state['filesizeread']) + \
                                                                len(self.json_data[self.name])
                    self.solr_post_json_data(pf_base)
                    parser.write_file_state(file_state)
                    parser.set_parsed_size(pf_base,file_state['filesizeread'])                                          # устанавливаю размер на количетво распарсенных данных
                else:                                                                                                   # в ret ничего не вернулось
                    t.debug_print("no rows was returned",self.name)
                    time.sleep(g.waits.read_state_exception)                                                            # чтобы не нагружать в цикле CPU на базах, которых не удалось прочитать файл. Например, отсутствующих на кластере
                    return
            # сохраняем текущий статус парсинга ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        except Exception as e:
            t.debug_print("parse lgd file "+pf_name+" on base "+ pf_base +" got exception:"+str(e),self.name)
    # ------------------------------------------------------------------------------------------------------------------
    # разбор и индексирование одного файла старого формата
    # ------------------------------------------------------------------------------------------------------------------
    def parse_lgp_file(self, pf_name, pf_base):                                                                           # обработка файла старого формата
        t.debug_print("processing " + pf_name,self.name)                                                                # слишком много текстов буде
        file_state                                          =   {}
        # Проверка наличия файла ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if not os.path.exists(pf_name):
            t.debug_print(f"file not found {pf_name}", self.name)
            return
        # Готовлюсь к чтению ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        pf_size                                             =   os.stat(pf_name).st_size                                # текущий размер файла
        file_state['filename']                              =   pf_name                                                 # локальная структура json с именем файла
        file_state['filesize']                              =   pf_size                                                 # локальная структура json с размером файла
        file_state['filesizeread']                          =   parser.read_file_state(pf_name,file_state['filesize'])  # пытаюсь получить размер прочитанных байт из сохранённого состояния
        # Немного переменных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        pf_block_mul                                        =   1                                                       # мультипликатор для блоков.
        #pf_match_no                                         =   0                                                       # номер записи
        pf_bytes_2_commit                                   =   0
        dt_sort_add                                         =   0                                                       # переменная доп. нумерации дополнительного поля сортировки дат
        prev_r1                                             =   ""                                                      # значение для хранения дат из предудущей записи
        block_time_start                                    =   None
        block_commit_start                                  =   time.time()
        try:                                                                                                            # всё в попытке
            # чтение остатка содержимого файла в байтах ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            while file_state['filesizeread']                <   pf_size:                                                # пока смещением не дошёл до конца
                t.debug_print(
                    f"file={pf_name} base={pf_base} read={str(file_state['filesizeread'])}",
                    self.name
                )
                if g.debug.on_parser and block_time_start:
                        t.debug_print(f"Block tooked {str(time.time()-block_time_start)}",self.name)
                block_time_start                            =   time.time()                                             # фиксация времени начала обработки блока
                d.read_ib_dictionary(pf_base)                                                                           # словарь должен быть уже проинициализирован
                # определяю размер для чтения ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                pf_size_read                                =   g.parser.blocksize * pf_block_mul                       # размер блока для чтения
                # обработка корявых фрагментов ЖР ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                if pf_size_read                             >   g.parser.maxblocksize:                                  # если превышен макс размер блока для чтения
                    pf_size_read                            =   g.parser.maxblocksize                                   # блок оставляем маскимальным
                    file_state['filesizeread']              +=  g.parser.maxblocksize//2                                # и перемещаем маркер чтения на половину максимального блока вперёд
                    t.debug_print(pf_base+':bad block detected, skipping to '+str(file_state['filesizeread']),self.name)
                # вычисляю сколько нужно читать ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+ https://github.com/WonderMr/Journal2Ct/issues/40
                pf_delta                                    =   pf_size - file_state['filesizeread']
                # сначала проверю, не меньши ли файл блока для чтения ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                pf_rest_bytes                               =   pf_delta                        \
                                                                if pf_delta > 0                 \
                                                                else pf_size
                                                                # вычисляю остаток для чтения
                # теперь - размер блока для чтения. Если он больше остатка байт для чтения, то
                pf_size_read                                =   pf_size_read                    \
                                                                if pf_rest_bytes > pf_size_read \
                                                                else pf_rest_bytes                                      # если остаток для чтения больше размера блока, то считываем размер блока, иначе - остаток файла
                # иду к смещению и читаю блок ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                pf_chunk                                    =   self.read_block(
                                                                    pf_name,
                                                                    file_state['filesizeread'],
                                                                    pf_size_read
                                                                )
                # конвертация байтов в строку ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                if pf_chunk:                                                                                            # если данные есть
                    pf_chunk_converted                      =   False                                                   # получилось ли их перегнать в строку?
                    while not pf_chunk_converted:                                                                       # пока не получится
                        try:                                                                                            # пробую декодировать
                            pf_block_as_str                 =   pf_chunk.decode(encoding='UTF8')                        # пробую декодировать
                            pf_chunk_converted              =   True                                                    # получилось
                        except Exception as e:                                                                          # не получилось,
                            if g.debug.on_parser:
                                t.debug_print(
                                    pf_base+":Bad symbol while decoding chunk in " + pf_name + " " + str(e),
                                    self.name
                                )
                            mesg                            =   str(e)
                            position                        =   g.rexp.bad_chunk_pos.findall(mesg)
                            if position and len(position)>0:                                                            # если есть сообщение об ошибке декодирования с позицией проблемного байте
                                if int(position[0])         >   0:                                                      # и если оно спереди
                                    if g.debug.on_parser:
                                        t.debug_print(pf_base+":chunk decrease to "+position[0],self.name)
                                    pf_chunk                =   pf_chunk[0:int(position[0])]                            # то уменьшаюсь до его размера
                                else:                                                                                   # если не декодируется с начала блока
                                    if g.debug.on_parser:
                                        t.debug_print(pf_base+":chunk -1 going forward", self.name)
                                    file_state['filesizeread']\
                                                            -=  1                                                       # то читаем на байт сзади. Такое авно только для поверждённых кусков бывает
                                    pf_chunk                =   self.read_block(
                                                                    pf_name,
                                                                    file_state['filesizeread'],
                                                                    pf_size_read
                                                            )
                            else:
                                t.debug_print(pf_base+":Exception: всё очень плохо, я не придумал что с этим делать"
                                              ,self.name)
                    # получаю все записи из строки ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    pf_records                              =   g.rexp.my_parse_re.findall(pf_block_as_str)             # вот это все мои записи ЖР
                    if pf_records:                                                                                      # если они есть
                        for pf_record in pf_records:                                                                    # то пройдёмся по ним
                            #pf_match_no                     +=  1                                                       # номер записи
                            # разбираю каждую запись на составные ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            # pf_rec_parsed                   =   g.rexp.my_sel_re.findall(pf_record)                     # разбираю запись на составные
                            if(g.debug.on_parser):
                                t.debug_print("processing pf_record "+str(pf_record),self.name)
                            pf_rec_in_bytes                 =   str(pf_record[0]).encode(encoding='UTF8')               # чтобы найти смещение записи кодирую её
                            pf_rec_parsed                   =   pf_record[1:]                                           # копирую в такой же элемент, только без первой строки
                            if(g.debug.on_parser):
                                t.debug_print("processing pf_rec_parsed "+str(pf_rec_parsed),self.name)
                            pf_rec_offset                   =   file_state['filesizeread'] \
                                                            +   pf_chunk.find(pf_rec_in_bytes)                          # и нахожу смещение
                            if (prev_r1                     ==  pf_rec_parsed[0][0]):                                   # если дата совпадает
                                dt_sort_add                 +=  1
                            else:
                                dt_sort_add                 =   0
                            # добавляю в перменную класса json_data данные из очередной записи ~~~~~~~~~~~~~~~~~~~~~~~~~
                            #if(parser.check_rec(pf_name,pf_rec_offset,len(pf_rec_in_bytes))):                          # эта была проверка для каждой добавляемой записи
                            pf_rec_parsed                   =   self.fix_act_tran(pf_rec_parsed,pf_base)                # вот она, знаменитаю функция исправления дурацкого статуса транзакци транзакций
                            m.check_event(pf_rec_parsed, pf_base)
                            if not self.add_to_json_data    (
                                                                pf_rec_parsed,
                                                                dt_sort_add,
                                                                pf_name,
                                                                pf_rec_offset,
                                                                len(pf_rec_in_bytes),
                                                                pf_base
                                                            ):                                                          # добавлю данные текущей записи, моменте времени для сортировки, имени файла и её смщения в глобальный массив
                                t.debug_print("Exception : can't append "+str(pf_rec_parsed))
                            #t.debug_print(r.reader.read_rec(test))                                               test stuff
                            prev_r1                         =   pf_rec_parsed[0][0]
                            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        # освежаю переменные после завершения парсинга очередного блока ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        pf_last_rec                         =   pf_records[len(pf_records) - 1]                         # извлекаю последную запись
                        ps_last_rec_in_bytes                =   str(pf_last_rec[0]).encode(encoding='UTF8')             # заворачиваю её в байты
                        pf_last_pos                         =   pf_chunk.rfind(ps_last_rec_in_bytes)                    # нахожу её позицию
                        pf_last_rec_bytes_len               =   pf_last_pos + len(ps_last_rec_in_bytes)                 # это - смещение после последней обработанной записи
                        file_state['filesizeread']          +=  pf_last_rec_bytes_len                                   # увеличиваю смещение на позицию последней записи и её длину в байтах
                        #t.debug_print('filesizeread = ' + str(file_state['filesizeread']))
                        pf_block_mul                        =   1                                                       # освобождаю мультипликаторв блока
                        pf_bytes_2_commit                   +=  pf_last_rec_bytes_len                                   # размер байт для коммита
                        #t.debug_print('pf_bytes_2_commit = ' + str(pf_bytes_2_commit))
                        # проверяю необходимость коммита и осуществляю его ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        if  pf_bytes_2_commit               >   g.parser.bytes_2_commit or \
                            file_state['filesizeread']      ==  file_state['filesize']:
                                t.debug_print(  pf_base+":commiting with state: \n" +
                                                "total length     = "        +  str(file_state['filesize'])     + "\n"+
                                                "new curr. length = "        +  str (
                                                                                    file_state['filesizeread']  +
                                                                                    len(self.json_data[self.name])
                                                                                )                               + "\n"+
                                                "current length   = "        +  str(file_state['filesizeread']) + "\n"+
                                                "commited records = "        +  str(
                                                                                    len(self.json_data[self.name])),
                                                                                    self.name
                                                                                )                                       # add 2019.02.15 для https://github.com/WonderMr/Journal2Ct/issues/40
                                if block_time_start:
                                    t.debug_print(
                                        "Block before commit " + str(time.time() - block_commit_start),
                                        self.name
                                    )
                                    block_commit_start      =   time.time()
                                self.solr_post_json_data(pf_base)                                                       # отправляем данные
                                parser.write_file_state(file_state)
                                # увеличиваю размер на количетво распарсенных данных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                parser.inc_parsed_size(pf_base, pf_bytes_2_commit)                                      # увеличиваю размер на количетво распарсенных данных
                                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                pf_bytes_2_commit           =   0                                                       # обнуляю сумматор байт для отправки
                    else:
                        if (pf_size - pf_size_read)         ==  file_state['filesizeread']:                             # если дочитали файл до конца, но записей ЖР не нашли
                            t.debug_print(  pf_base+":commiting(strange) with state: \n"  +
                                            "total length     = "         + str(file_state['filesize'])     + "\n" +
                                            "new curr. length = "         + str(
                                                                                file_state['filesizeread']  +
                                                                                len(self.json_data[self.name])
                                                                            )                               + "\n" +
                                            "current length   = "         + str(file_state['filesizeread']) + "\n" +
                                            "commited records = "         + str(
                                                                                len(self.json_data[self.name])),
                                                                                self.name
                                                                            )                                           # add 2019.02.15 для https://github.com/WonderMr/Journal2Ct/issues/40
                            file_state['filesizeread']      =   pf_size                                                 # закрываем чтение
                            if(len(self.json_data[self.name])>  0):                                                     # если есть неотправленные данные
                                if block_time_start:
                                    t.debug_print("Block tooked before commit " + str(time.time() - block_commit_start))
                                    block_commit_start      =   time.time()
                                self.solr_post_json_data(pf_base)                                                       # отправляем данные
                                # увеличиваю размер на количетво распарсенных данных ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                parser.inc_parsed_size(pf_base,pf_size_read)                                            # увеличиваю размер на количетво распарсенных данных
                                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                pf_bytes_2_commit           =   0
                            parser.write_file_state(file_state)                                                         # и заносим сведения об этом в файл
                        else:
                            pf_block_mul                    *=  2                                                       # разобрать блок на записи ЖР не получилось, увеличиваю мультипликатор
                            t.debug_print("Block too large. Current size is " + str(g.parser.blocksize * pf_block_mul))
                else:
                    t.debug_print(pf_base+":got empty chunk on file "+pf_name+" with pos="+file_state['filesizeread'])
        except Exception as e:
            t.debug_print(pf_base+":Exception # parse_file got error " + str(e),self.name)
    # ------------------------------------------------------------------------------------------------------------------
    # read part of file - читаю кусочек файла по смещению
    # ------------------------------------------------------------------------------------------------------------------
    def read_block(self,rb_name,rb_offset,rb_size):
        try:
            rb_fh                                               =   open(rb_name, 'rb')                                 # открываю файл
            rb_fh.seek(rb_offset)                                                                                       # иду к смещению
            rb_chunk                                            =   rb_fh.read(rb_size)                                 # читаю его
        except Exception as e:
            t.debug_print("Exception11 while read file "+rb_name,self.name)
        finally:
            rb_fh.close()
        return rb_chunk
    # ------------------------------------------------------------------------------------------------------------------
    # читаю информацию о статус обработки файла данных в файле статусов
    # ------------------------------------------------------------------------------------------------------------------
    def read_file_state(rfs_name, rfs_size):                                                                            # читаю информацию о закомиченных данных в файле статусов
        if os.path.exists(g.parser.state_file):                                                                         # если файл статуса есть
            while g.parser.state_file_lock:                                                                             # если файл заперт, то ждём
                time.sleep(g.waits.in_cycle_we_trust)
            g.parser.state_file_lock                        =   True                                                    # запираем state
            rfs_done                                        =   False
            while not rfs_done:                                                                                         # делаем, пока не получится
                # поищем в кэше ----------------------------------------------------------------------------------------
                for rfs_elem in g.cache.filesizes:
                    if rfs_name == rfs_elem['filename'] and rfs_size == rfs_elem['filesize']:
                        g.parser.state_file_lock            =   False
                        return rfs_elem['filesizeread']                                                                 # возвращаем из кэша
                try:
                    # в кэше нету --------------------------------------------------------------------------------------
                    del g.cache.filesizes[:]                                                                            # чистим его
                    rfs_found                               =   False                                                   # запись найдена в файле
                    rfs_handle                              =   open(g.parser.state_file, 'r', encoding='UTF8')         # открываю файл статуса
                    rfs_context                             =   rfs_handle.read()                                       # читаем файл статуса
                    rfs_handle.close()                                                                                  # закрываю хэндл
                    try:
                        rfs_json                            =   json.loads(rfs_context)                                 # читаю содержимое
                        # заполняем кэш --------------------------------------------------------------------------------
                        for rfc_rec in rfs_json:                                                                        # по всем записям
                            rfc_local                       =   {}
                            rfc_local['filename']           =   rfc_rec['filename']
                            rfc_local['filesizeread']       =   rfc_rec['filesizeread']
                            rfc_local['filesize']           =   rfc_rec['filesize']
                            g.cache.filesizes.append(rfc_local)
                        # ищем уже в кэше ------------------------------------------------------------------------------
                        for rfs_elem in g.cache.filesizes:
                            if rfs_elem['filename']         ==  rfs_name:                                               # если такой файл есть
                                rfs_found                   =   True
                                g.parser.state_file_lock    =   False
                                return rfs_elem['filesizeread']                                                         # сколько уже прочитанно
                    except Exception as e:
                        t.debug_print("read_file_state got Exception while parsing state file " + str(e))
                        sys.exit(-1)
                    if not rfs_found:                                                                                   # в файле такой записи нет
                        g.parser.state_file_lock            =   False  # отпираем state
                        return 0                                                                                        # возвращаем 0
                except Exception as e:
                    t.debug_print("read_file_state got Exception"+str(e))
                finally:
                    g.parser.state_file_lock                =   False                                                   # отпираем state
                    rfs_handle.close()
                    rfs_done                                =   True
            if not rfs_done:
                time.sleep(g.waits.read_state_exception)                                                                # ждём таймаут
        else:                                                                                                           # если файла нет,
            return 0                                                                                                    # возвращаем ноль
    # ------------------------------------------------------------------------------------------------------------------
    # сохраняю информацию о статус обработки файла в файле статусов
    # ------------------------------------------------------------------------------------------------------------------
    def write_file_state(ws_json):                                                                                      # сохраняет статус обработки файлов
        ws_done                                             =   False
        if os.path.exists(g.parser.state_file):                                                                         # если state-файл уже есть
            while g.parser.state_file_lock:                                                                             # если файл заперт, то ждём
                time.sleep(g.waits.in_cycle_we_trust)
            g.parser.state_file_lock                        =   True                                                    # запираем state
            while not ws_done:
                try:
                    ws_handle                               =   open(g.parser.state_file, 'r+', encoding='UTF8')
                    ws_state                                =   ws_handle.read()
                    ws_found                                =   False
                    try:
                        ws_state_json_arr                   =   json.loads(ws_state)
                        for ws_json_rec in ws_state_json_arr:
                            if(ws_json_rec['filename']      ==  ws_json['filename']):
                                ws_json_rec['filesize']     =   ws_json['filesize']
                                ws_json_rec['filesizeread'] =   ws_json['filesizeread']
                                ws_found                    =   True
                    except Exception as e:
                        t.debug_print("write_file_state got error while parsing state json "+str(e))
                    if not ws_found:
                        if 'ws_state_json_arr' in locals():                                                             # если массив вообще есть
                            ws_state_json_arr.append(ws_json)                                                           # дополняем его
                        else:                                                                                           # иначе пилим новый массив
                            ws_state_json_arr               =   []
                            ws_state_json_arr.append(ws_json)
                    ws_handle.close()
                    ws_handle                               =   open(g.parser.state_file, 'w', encoding='UTF8')
                    json.dump(ws_state_json_arr, ws_handle, indent=2)
                    ws_done                                 =   True
                except Exception as e:
                    t.debug_print("write_file_state got Exception "+str(e))
                finally:
                    ws_handle.close()
                    g.parser.state_file_lock                =   False                                                   # отпираем state
                if not ws_done:
                    time.sleep(g.waits.read_state_exception)                                                            # ждём таймаут
        else:                                                                                                           # если же создаём state-файл
            while not ws_done:
                g.parser.state_file_lock                    =   True                                                    # запираем state
                try:
                    ws_state_json_arr                       =   []
                    ws_state_json_arr.append(ws_json)
                    ws_handle                               =   open(g.parser.state_file, 'w', encoding='UTF8')
                    json.dump(ws_state_json_arr, ws_handle, indent=2)
                except Exception as e:
                    t.debug_print("write_file_state got Exception"+str(e))
                finally:
                    ws_handle.close()
                    g.parser.state_file_lock                =   False                                                   # отпираем state
                    ws_done                                 =   True
                if not ws_done:
                    time.sleep(g.waits.read_state_exception)                                                            # ждём таймаут
    #-------------------------------------------------------------------------------------------------------------------
    # увеличиваю размер распарсенных данных для базы
    # ------------------------------------------------------------------------------------------------------------------
    def inc_parsed_size(base,count):
        for each in g.parser.ibases:
            if each[g.nms.ib.name]                          ==  base:
                each[g.nms.ib.parsed_size]                  +=  count
    #-------------------------------------------------------------------------------------------------------------------
    # устанавливаю размер всего для базы
    # ------------------------------------------------------------------------------------------------------------------
    def set_total_size(base,sts_size):
        for each in g.parser.ibases:
            if each[g.nms.ib.name]                          ==  base:
                each[g.nms.ib.total_size]                   =   sts_size
    #-------------------------------------------------------------------------------------------------------------------
    # получаю размер всего для базы
    # ------------------------------------------------------------------------------------------------------------------
    def get_total_size(base):
        for each in g.parser.ibases:
            if each[g.nms.ib.name]                          ==  base:
                return each[g.nms.ib.total_size]
    #-------------------------------------------------------------------------------------------------------------------
    # устанавливаю размер распарсенных данных для базы
    # ------------------------------------------------------------------------------------------------------------------
    def set_parsed_size(base,count):
        for each in g.parser.ibases:
            if each[g.nms.ib.name]                          ==  base:
                each[g.nms.ib.parsed_size]                  =   count
    #-------------------------------------------------------------------------------------------------------------------
    # функция исправления дурацкого статуса транзакции при парсинге
    # ------------------------------------------------------------------------------------------------------------------
    def fix_act_tran(self, pf_rec, pf_base):
        try:
            pf_ret                                          =   pf_rec
            if g.execution.c1_dicts.tran_fix_list.get(pf_base):
                if pf_rec[8]                                in  g.execution.c1_dicts.tran_fix_list[pf_base]:            # в списке бэдовых, исправляю
                    tpl                                     =   {}
                    tpl[0]                                  =   pf_rec[0]
                    if pf_rec[1]                            ==  "C":
                        tpl[1]                              =   "U"
                    elif pf_rec[1]                          ==  "R":
                        tpl[1]                              =   "C"
                    elif pf_rec[1]                          ==  "U":
                        tpl[1]                              =   "R"
                    else:
                        tpl[1]                              =   "N"
                    for l_i in range(2,len(pf_rec)):                                                                    #case 2020.05.21
                        tpl[l_i]                            =   pf_rec[l_i]                                             #case 2020.05.21
                    pf_ret                                  =   tpl
                else:
                    pf_ret                                          =   pf_rec                                                  # возвращаю то же самое, если ничего не менять
        except Exception as e:
            t.debug_print("Fix tran got exception "+str(e),self.name)
        finally:
            return pf_ret
# ======================================================================================================================