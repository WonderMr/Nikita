# _*_ coding: UTF-8 _*_
import  sys, os, configparser
import  win32timezone                                                                                                   # нужен для скомпилированного
import  win32serviceutil, win32service, win32event, servicemanager, winerror
import  psutil
import  time
import  multiprocessing
import  re
import  threading
# fix https://github.com/pypa/setuptools/issues/1963 ===================================================================
#import pkg_resources.py2_warn
#del pkg_resources.py2_warn
# ======================================================================================================================
from distutils.util         import  strtobool
# ======================================================================================================================
from    src                 import  parser                  as  p
from    src.reader          import  reader                  as  r
from    src.dictionaries    import  dictionary              as  d
from    src                 import  cherry                  as  c
from    src.tools           import  tools                   as  t
from    src                 import  solr                    as  s
from    src                 import  globals                 as  g
# ======================================================================================================================
# собственно, сервис windows
# ======================================================================================================================
class journal2ct_service(win32serviceutil.ServiceFramework):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    _svc_name_                                              =   g.service.name
    _svc_display_name_                                      =   g.service.display_name
    _svc_description_                                       =   g.service.description
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop                                      =   win32event.CreateEvent(None, 0, 0, None)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SvcStop(self):
        stop_exp                                            =   ""
        try:
            t.debug_print('service stop')
            stop_exp                                        =   "ReportServiceStatus"
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            stop_exp                                        =   "stop"
            self.Stop                                       =   True
            stop_exp                                        =   "stop_all"
            stop_all()
            #stop_exp                                        =   "ReportServiceStatus"
            #self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            stop_exp                                        =   "SetEvent"
            win32event.SetEvent(self.hWaitStop)
        except Exception as e:
            t.debug_print("Exception1 "+str(e)+" exp is "+stop_exp)
        t.debug_print("Service stopped")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SvcDoRun(self):
        try:
            self.log("start")
            t.debug_print('service start')
            self.Stop                                       =   False
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            t.debug_print('service start threads')
            start_all()
            while self.Stop                                 ==  False:
                time.sleep(g.waits.in_cycle_we_trust)
            #win32event.WaitforSingleObject(self.hWaitStop, win32event.INFINITE)
        except Exception as e:
            t.debug_print("Exception2 "+str(e))
# ======================================================================================================================
# Определение, сохранение и загрузка конфигурации
# ======================================================================================================================
class conf:
    # ------------------------------------------------------------------------------------------------------------------
    # загрузка конфы
    # ------------------------------------------------------------------------------------------------------------------
    def load(fake_param=0):
        config                                              =   configparser.ConfigParser()
        config.read(g.conf.filename,encoding="UTF8")
        try:
            # ~~~~~~~ загружаю специфику 1С ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            try:
                c1i_exists                                  =   config[g.conf.c1.section_name]["ibase_0"]               # пытаюсь вынть первое значение
                i                                           =   0
                while c1i_exists:
                    try:
                        ibase_info                          =   {
                            g.nms.ib.name                   :   config[g.conf.c1.section_name]["ibase_"+str(i)],
                            g.nms.ib.jr_dir                 :   config[g.conf.c1.section_name]["ibase_"+str(i)+"_jr"],
                            g.nms.ib.jr_format              :   config[g.conf.c1.section_name]\
                                                                ["ibase_"+str(i)+"_format"],
                            g.nms.ib.total_size             :   0,
                            g.nms.ib.parsed_size            :   0
                        }
                        g.parser.ibases.append(ibase_info)
                        i                                   +=  1
                    except Exception as e:
                        c1i_exists                          =   False
                        pass
            except Exception as e:
                t.debug_print("В файле конфигурации нет информационных баз")
            # ~~~~~~~ загружаю специфику SOLR ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            g.conf.solr.mem_min                             =   config[g.conf.solr.section_name]["mem_min"]
            g.conf.solr.mem_max                             =   config[g.conf.solr.section_name]["mem_max"]
            g.conf.solr.dir                                 =   config[g.conf.solr.section_name]["dir"]
            g.conf.solr.listen_interface                    =   config[g.conf.solr.section_name]["listen_interface"]
            g.conf.solr.listen_port                         =   config[g.conf.solr.section_name]["listen_port"]
            g.conf.solr.solr_host                           =   config[g.conf.solr.section_name]["solr_host"]
            g.conf.solr.solr_port                           =   config[g.conf.solr.section_name]["solr_port"]
            g.conf.solr.java_home                           =   config[g.conf.solr.section_name]["java"]
            g.conf.solr.threads                             =   config[g.conf.solr.section_name]["threads"]

            # ~~~~~~~ загружаю специфику HTTP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            g.conf.http.listen_interface                    =   config[g.conf.http.section_name]["listen_interface"]
            g.conf.http.listen_port                         =   config[g.conf.http.section_name]["listen_port"]

            # ~~~~~~~ загружаю специфику парсера~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            g.parser.threads                                =   config[g.parser.section_name]["threads"]

            # ~~~~~~~ загружаю специфику отладки~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            try:
                g.debug.on                                  =   strtobool(config["debug"]["enabled"])
                t.debug_print("Debug enabled = "+str(g.debug.on))
            except:
                pass

            try:
                g.debug.on_parser                           =   strtobool(config["debug"]["debug_parser"])
                t.debug_print("Debug_parser enabled = "+str(g.debug.on_parser))
            except:
                pass

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        except Exception as e:
            t.debug_print("Error while parsing params "+str(e))
            t.seppuku()
    # ------------------------------------------------------------------------------------------------------------------
    # сохранение конфы
    # ------------------------------------------------------------------------------------------------------------------
    def save(fake_param                                     =   0):
        if g.conf.solr.dir == "":
            t.debug_print("Empty configuration will not be saved")
            return
        else:
            t.debug_print("Saving configiration")
        config                                              =   configparser.ConfigParser()
        # ~~~~~~~ Специфика 1С ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        config.add_section(g.conf.c1.section_name)
        i                                                   =   0
        for ibase in g.parser.ibases:
            config.set(g.conf.c1.section_name,  "ibase_" +  str(i)          , ibase[g.nms.ib.name])
            config.set(g.conf.c1.section_name,  "ibase_" +  str(i)+"_jr"    , ibase[g.nms.ib.jr_dir])
            config.set(g.conf.c1.section_name,  "ibase_" +  str(i)+"_format", ibase[g.nms.ib.jr_format])
            i                                               +=  1

        # ~~~~~~~ Специфика SOLR ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        config.add_section(g.conf.solr.section_name)
        config.set(g.conf.solr.section_name,    "mem_min",          g.conf.solr.mem_min)
        config.set(g.conf.solr.section_name,    "mem_max",          g.conf.solr.mem_max)
        config.set(g.conf.solr.section_name,    "dir",              g.conf.solr.dir)
        config.set(g.conf.solr.section_name,    "listen_interface", g.conf.solr.listen_interface)
        config.set(g.conf.solr.section_name,    "listen_port",      g.conf.solr.listen_port)
        config.set(g.conf.solr.section_name,    "solr_host",        g.conf.solr.solr_host)
        config.set(g.conf.solr.section_name,    "solr_port",        g.conf.solr.solr_port)
        config.set(g.conf.solr.section_name,    "java",             g.conf.solr.java_home)
        config.set(g.conf.solr.section_name,    "threads",          g.conf.solr.threads)

        # ~~~~~~~ Специфика HTTP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        config.add_section(g.conf.http.section_name)
        config.set(g.conf.http.section_name,    "listen_interface", g.conf.http.listen_interface)
        config.set(g.conf.http.section_name,    "listen_port",      g.conf.http.listen_port)

        # ~~~~~~~ Специфика парсера ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        config.add_section(g.parser.section_name)
        config.set(g.parser.section_name,       "threads",          g.parser.threads)

        # ~~~~~~~ Специфика отладка~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        config.add_section("debug")
        config.set("debug","enabled",str(g.debug.on))

        # ~~~~~~~ Сохраняем ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        config_file_handle                                  =   open(g.conf.filename,'w',encoding="UTF8")
        config.write(config_file_handle)
        config_file_handle.close()
    # ------------------------------------------------------------------------------------------------------------------
    # определение настроек по умлочанию
    # ------------------------------------------------------------------------------------------------------------------
    def detect(fake_param=0,initial=False):
        t.debug_print("Conf detection")
        # ~~~~~~~ получение первой активной службы 1C ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        d_found                                             =   False
        for service in psutil.win_service_iter():
            try:
                d_service                                   =   (psutil.win_service_get(service.name())).as_dict()
            except Exception as e:
                t.debug_print("failed to parse "+str(service),'detect')
            if g.rexp.service_is_1c.search(d_service["binpath"]) and d_service["start_type"] == 'automatic':
                t.debug_print("found "+d_service["binpath"])
                d_found                                     =   True
                try:
                    #g.conf.c1.srvinfo                      =   g.rexp.service_1c_workdir.findall(service.binpath())[0]   #берем только первое значение
                    detect_srvinfos                         =   g.rexp.service_1c_workdir.findall(service.binpath())
                    if not len(detect_srvinfos)>0 :
                        t.debug_print("can't detect srvinfo")
                        t.seppuku()
                    srv_dir                                 =   re.sub(r'\\\\\\','\\\\' ,detect_srvinfos[0])
                    thread_name                             =   g.threads.config_updater.name \
                                                                if g.threads.config_updater \
                                                                else "initial configuration detection"
                    t.debug_print("processing "+srv_dir,thread_name)
                    conf.detect2(initial2=initial,d2_srvinfo=srv_dir)
                except Exception as e:
                    t.debug_print("Exception srv_1c "+str(e))
        if not d_found:
            t.debug_print("1C services not found")
            t.seppuku()
    # ~~~~~~~ получение списка баз и кластеров 1C ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def detect2(fake_param=0,initial2=False,d2_srvinfo=""):
        regs                                                =   [element for element
                                                                    in os.listdir(d2_srvinfo)
                                                                        if os.path.isdir(d2_srvinfo+"\\"+element)
                                                                            and g.rexp.is_1c_cluster.findall(element)
                                                                ]                                                       # получаю списков все кластеров
        local_bases_array                                   =   []
        t.debug_print("regs="+str(regs))
        for reg in regs:
            clstr_dir                                       =   d2_srvinfo+"\\"+reg
            t.debug_print("clstr_dir=" + str(clstr_dir))
            clstr_file                                      =   clstr_dir + "\\" + g.conf.c1.cluster_file
            clstr_file_o                                    =   clstr_dir + "\\" + g.conf.c1.cluster_file_o
            clstr_file_o                                    =   clstr_file_o if os._exists(clstr_file_o) \
                                                                else clstr_file                                         # сегодня (2020.05.22) столкнулся с отсутствием c cluster_file_o
            clstr_file_size                                 =   os.stat(clstr_file).st_size \
                                                                if os.path.exists(clstr_file) \
                                                                else 0
            clstr_file_o_size                               =   os.stat(clstr_file_o).st_size \
                                                                if os.path.exists(clstr_file_o) \
                                                                else 0
            clstr_file                                      =   clstr_file_o \
                                                                if clstr_file_size > clstr_file_o_size \
                                                                else clstr_file                                         # предпочитаем читать файл большего размера, если он есть
            if not os.path.isfile(clstr_file):
                t.debug_print("no cluster file found with "+str(clstr_file))
                return
            else:
                t.debug_print("processing "+str(clstr_file))
            clstr_handle                                    =   open(clstr_file, 'r', encoding='UTF8')
            clstr_text                                      =   clstr_handle.read()
            clstr_handle.close()
            clstrs                                          =   g.rexp.clst_1c_base_rec.findall(clstr_text)
            t.debug_print("found clusters="+str(clstrs))
            for clst in clstrs:
                ibase_dir                                   =   clstr_dir+"\\"+clst[0]
                ibase_jr_dir                                =   ibase_dir+"\\"+g.conf.c1.jr_dir
                ibase_jr_dir                                =   re.sub(r'\\\\\\', '\\\\' ,ibase_jr_dir)                 # https://github.com/WonderMr/Journal2Ct/issues/38
                if(os.path.exists(ibase_jr_dir)):                                                                       # каталог журнала регистрации есть
                    ibase_jr_new_fname                      =   ibase_jr_dir+"\\"+g.conf.c1.jr_new_fname                # имя файла нового формата жр
                    ibase_jr_new                            =   os.path.exists(ibase_jr_new_fname)
                    ibase_jr_old_dict_fname                 =   ibase_jr_dir+"\\"+g.conf.c1.jr_old_dict_fname           # имя файла словаря старого формата жр
                    ibase_jr_old                            =   os.path.exists(ibase_jr_old_dict_fname)                 # если ли файл словаря старого формата ЖР
                    if(ibase_jr_new or ibase_jr_old):
                        ib_nm                               =   t.normalize_ib_name(clst[1].upper())
                        ibase_info                          =   {
                            g.nms.ib.name                   :   ib_nm,
                            g.nms.ib.jr_dir                 :   ibase_jr_dir,
                            g.nms.ib.jr_format              :   g.nms.ib.jr_format_new
                                                                if ibase_jr_new else
                                                                g.nms.ib.jr_format_old,
                            'total_size'                    :   0,
                            'parsed_size'                   :   0
                        }                                                                                               # формирую dictionary с информацией о базе
                        if not initial2:                                                                                # !!!если первоначальное, то не определяем базы!!!
                            base_found                      =   False
                            local_bases_array.append(ibase_info)                                                        # добавляю в локальный массив, чтобы определить удалённые базы
                            for base in g.parser.ibases:
                                if base[g.nms.ib.name]      ==  ibase_info[g.nms.ib.name]:
                                    base_found              =   True
                            if not base_found:
                                t.debug_print("Обнаружена новая ИБ:"+ ibase_info[g.nms.ib.name])
                                #if g.threads.solr.check_base_exists(cbe_name=ibase_info[g.nms.ib.name]):                # если здесь новоя ядрышко создастся
                                if True:
                                    g.parser.ibases.append(ibase_info)                                                  # добавляю его в массив

        if not initial2:                                                                                                # проверяю базы на удалённые
            bases_copy                                      =   g.parser.ibases.copy()                                  # из этой копии будем удалять базы
            for each_base in local_bases_array:                                                                         # по всем базам из файла
                for each_each_base in bases_copy:                                                                       # по всем из копии конфы
                    if each_base[g.nms.ib.name]             ==  each_each_base[g.nms.ib.name]:                          # если есть, то убираем из копии. Уйти должны все существующие
                        bases_copy.remove(each_each_base)
            for each_base in bases_copy:                                                                                # а вот оставшиеся - это удалённые
                if(str(each_base[g.nms.ib.jr_dir]).find(d2_srvinfo))>0:                                                 # удаляем только базы этого кластера
                    t.debug_print("База "+each_base[g.nms.ib.name]+" удалена с кластера")
                    g.parser.ibases.remove(each_base)
        # ~~~~~~~ установка параметров solr по умолчанию для первого детекта ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if initial2:
            g.conf.solr.mem_min                             =   "2g"
            g.conf.solr.mem_max                             =   "32g"
            g.conf.solr.dir                                 =   g.execution.self_dir+"solr"
            g.conf.solr.listen_interface                    =   "127.0.0.1"
            g.conf.solr.listen_port                         =   "8983"
            g.conf.solr.solr_host                           =   "127.0.0.1"                                             # socket.gethostbyaddr(g.conf.solr.listen_interface)
            g.conf.solr.solr_port                           =   "8983"
            g.conf.solr.java_home                           =   g.execution.self_dir+"java"
            g.conf.solr.threads                             =   str(multiprocessing.cpu_count() // 2)                   # половину ядер на solr
            # ~~~~~~~ установка параметров http по умолчанию ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            g.conf.http.listen_port                         =   "8984"
            g.conf.http.listen_interface                    =   "0.0.0.0"
            # ~~~~~~~ установка парсинга по умолчанию ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            use_cores                                       =   multiprocessing.cpu_count() // 2                        # используем только половину ядер по умолчанию
            i_count_bases                                   =   len(g.parser.ibases)                                    # сколько у нас есть баз
            g.parser.threads                                =   str(use_cores) \
                                                                if i_count_bases > use_cores else \
                                                                str(i_count_bases)                                      # если баз больше, чем ядер. То макс - половина ядер.
                                                                                                                        # если больше ядер - то исчисляем по списку баз
# ======================================================================================================================
# самая начальная инициализация переменных
# ======================================================================================================================
def init_vars():
    if getattr(sys, 'frozen', False):                                                                                   # если это exe
        g.execution.self_name                               =   str(sys.executable)
    else:  # если в отладке
        g.execution.self_name                               =   str(os.path.abspath(__file__))
    g.conf.filename                                         =   g.rexp.any_file_ext.sub('' ,   g.execution.self_name) \
                                                                +   "ini"                                               # имя файла конфигурации 2019.11.24 Я поймал какой-то странный глюк - двоится при замене. Поэтому сделал так
    g.execution.self_dir                                    =   g.rexp.any_filename.sub(''    ,   g.execution.self_name)# каталог с исполняемым файлом
    g.debug.dir                                             =   g.execution.self_dir+'debug\\'                          # каталог для хранения данных отладки
    g.debug.filename                                        =   g.debug.dir\
                                                            +   g.rexp.any_file_ext.sub(
                                                                    '',
                                                                    g.rexp.any_filename.search(g.conf.filename)[0])\
                                                            +   str(os.getpid())\
                                                            +   '.log'
    g.parser.state_file                                     =   g.execution.self_dir+"\\parser.state"                   # здесь в json хранятся статусы парсинга файлов
    g.parser.solr_id_file                                   =   g.execution.self_dir + "\\solr.id.state"                # здесь в json хранятся ID файлов для SOLR
# ======================================================================================================================
# дополнительная инициализация после загрузки/определения параметров
# ======================================================================================================================
def post_init_vars():
    g.execution.solr.url_main                               =   "http://" + g.conf.solr.solr_host+":"\
                                                            +   g.conf.solr.solr_port\
                                                            +   "/solr"
# ======================================================================================================================
# запускает все потоки парсинга, solr и веб-сервер
# ======================================================================================================================
def start_all(wait=False):
    try:
        t.debug_print("Starting all threads")
        # ~~~~~~~ загружаю или создаю конфигурацию ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if(os.path.exists(g.conf.filename)):
            t.debug_print("Load configuration")
            conf.load()
        else:
            t.debug_print("Configuration detection")
            conf.detect(initial=True)
            conf.save()
        post_init_vars()
        # ~~~~~~~ запускаю cherrypy в фоне ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.cherry                                    =   c.cherry_thread("my little cherry")
        g.threads.cherry.start()
        # ~~~~~~~ запускаю solr в фоне ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #g.threads.solr                                      =   s.solr_thread("my pretty solr thread")
        #g.threads.solr.start()
        # ~~~~~~~ до парсера надо дёрнуть словари ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for ib in g.parser.ibases:
            d.read_ib_dictionary(ib['ibase_name'])
        # ~~~~~~~ создаю и запускаю потоки парсеров ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.parser                                    =   p.parser("lgp")
        g.threads.parser.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~ создаю и запускаю потоки парсеров для нового формата ЖР ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.parser_new                                =   p.parser("lgd")
        g.threads.parser_new.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~ создаю и запускаю потоки парсеров для обновления списка баз ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.config_updater                            =   config_updater("IB monitor")
        g.threads.config_updater.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~ создаю и запускаю потоки парсеров для прогревания кэша ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #g.threads.warming_cache                             =   warming_cache("warming cache")
        #g.threads.warming_cache.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~ создаю и запускаю потоки парсеров ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #g.threads.parser2                                    =   p.parser("lgp")
        #g.threads.parser2.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~ создаю и запускаю потоки парсеров для нового формата ЖР ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #g.threads.parser_new2                                =   p.parser("lgd")
        #g.threads.parser_new2.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        while wait:
            time.sleep(g.waits.in_cycle_we_trust)
    except Exception as e:
        t.debug_print("Exception3 "+str(e))
# ======================================================================================================================
# поток мониторинга изменений баз
# ======================================================================================================================
class config_updater(threading.Thread):
    run                                                     =   True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name
        t.debug_print("Thread initialized", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        while self.run:
            try:
                time.sleep(g.waits.sleep_on_conf_detection)
                conf.detect(initial                         =   False)                                                  # проверяем список баз
                conf.save()
            except Exception as e:
                t.debug_print("Exception on confige update. Error is "+str(e))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        self.run                                            =   False
# ======================================================================================================================
# поток прогревания кэша
# ======================================================================================================================
class warming_cache(threading.Thread):
    run                                                     =   True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name
        t.debug_print("Thread initialized", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        while self.run:
            try:
                while not g.execution.solr.started:                                                                     # ждём, пока Solr проснётся
                    time.sleep(5)                                                                                       # ждём инициализации
                if isinstance(g.parser.ibases, list):
                    for i_base                              in g.parser.ibases:
                        if(i_base[g.nms.ib.parsed_size]     >   0):                                                     # только активные базы
                            t.debug_print("warming "+i_base[g.nms.ib.name]+" cache",self.name)
                            r.full_proceess_read("ref="+i_base[g.nms.ib.name]+"&КоличествоСобытий=1")
                time.sleep(g.waits.warming_cache_wait)
            except Exception as e:
                t.debug_print("Exception while warming cache. Error is "+str(e),self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        self.run                                            =   False
# ======================================================================================================================
# останавливает все потоки парсинга, solr и web-server
# ======================================================================================================================
def stop_all():
    try:
        # ~~~~~~~ останавливаю solr ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.solr.stop()
        # ~~~~~~~ останавливаю cherrypy ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.cherry.stop()#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # ~~~~~~~ останавливаю потоки парсера ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.parser.stop()#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # ~~~~~~~ останавливаю обновлятель списка баз ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.config_updater.stop()
        # ~~~~~~~ останавливаю подогреватель кэша ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.warming_cache.stop()
    except Exception as e:
        t.debug_print("Exception on stop all:"+str(e))
# ======================================================================================================================
# Go
# ======================================================================================================================
def main():
    init_vars()
    if ('console' in sys.argv):
        g.execution.running_in_console                  =   True
        start_all(wait                                  =   True)
    else:
        if len(sys.argv) == 1:
            # service must be starting...
            # for the sake of debugging etc, we use win32traceutil to see
            # any unhandled exceptions and print statements.
            print("Неверно указаны параметры\n"
                  "Для запуска в консольном режиме запустите с ключом 'console', \n"
                  "Для установки в качестве службы используйте ключ 'install'\n"
                  "Для запуска установленной службы - ключ 'start'\n"
                  "Для остановки службы - ключ 'stop'\n"
                  "Для удаления службы - ключ 'remove'")
            import win32traceutil
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(journal2ct_service)
            # Now ask the service manager to fire things up for us...
            servicemanager.StartServiceCtrlDispatcher()
            print("service done!")
        else:
            win32serviceutil.HandleCommandLine(journal2ct_service)

if __name__                                             ==  '__main__':
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        t.debug_print("Something went bad!")
        import traceback

        traceback.print_exc()
# ======================================================================================================================
