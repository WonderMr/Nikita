# _*_ coding: UTF-8 _*_
# Copyright (C) 2025 Nikita Development Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import platform
is_windows                                               = platform.system() == "Windows"
import  sys, os, configparser
if is_windows:
    import  win32timezone                                                                                               # нужен для скомпилированного
    import  win32serviceutil, win32service, win32event, servicemanager, winerror
else:
    import  subprocess
import  psutil
import  time
import  multiprocessing
import  re
import  threading
# fix https://github.com/pypa/setuptools/issues/1963 ===================================================================
#import pkg_resources.py2_warn
#del pkg_resources.py2_warn
# ======================================================================================================================
#from distutils.util         import  strtobool
# ======================================================================================================================
from    src                 import  parser                  as  p
from    src.reader          import  reader                  as  r
from    src.dictionaries    import  dictionary              as  d
from    src                 import  cherry                  as  c
from    src.tools           import  tools                   as  t
from    src                 import  solr                    as  s
from    src                 import  globals                 as  g
from    src                 import  redis_manager           as  rm
from    src                 import  sender                  as  snd
# ======================================================================================================================
# from distutils.util         import  strtobool replacement
# ======================================================================================================================
# ======================================================================================================================
# собственно, сервис windows
# ======================================================================================================================
if is_windows:
    class nikita_service(win32serviceutil.ServiceFramework):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        _svc_name_                                          =   g.service.name
        _svc_display_name_                                  =   g.service.display_name
        _svc_description_                                   =   g.service.description

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop                                  =   win32event.CreateEvent(None, 0, 0, None)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def log(self, msg):
            servicemanager.LogInfoMsg(str(msg))

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def SvcStop(self):
            stop_exp                                        =   ""
            try:
                t.debug_print('service stop')
                stop_exp                                    =   "ReportServiceStatus"
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                stop_exp                                    =   "stop"
                self.Stop                                   =   True
                stop_exp                                    =   "stop_all"
                stop_all()
                #stop_exp                                        =   "ReportServiceStatus"
                #self.ReportServiceStatus(win32service.SERVICE_STOPPED)
                stop_exp                                    =   "SetEvent"
                win32event.SetEvent(self.hWaitStop)
            except Exception as e:
                t.debug_print(f"Exception1 {str(e)} exp is {stop_exp}")
            t.debug_print("Service stopped")
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def SvcDoRun(self):
            try:
                self.log("start")
                t.debug_print('service start')
                self.Stop                                   =   False
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
                t.debug_print('service start threads')
                start_all()
                while self.Stop ==  False:
                    time.sleep(g.waits.in_cycle_we_trust)
                #win32event.WaitforSingleObject(self.hWaitStop, win32event.INFINITE)
            except Exception as e:
                t.debug_print(f"Exception2 {str(e)}")
# ======================================================================================================================
# Определение, сохранение и загрузка конфигурации
# ======================================================================================================================
class conf:
    # ------------------------------------------------------------------------------------------------------------------
    # загрузка конфы
    # ------------------------------------------------------------------------------------------------------------------
    def load(fake_param=0):
        config                                              =   configparser.ConfigParser()
        
        # Теперь читаем базы из ENV
        try:
            t.debug_print("Загрузка баз данных 1С из переменных окружения...")
            i                                               =   0
            while True:
                ibase_name                                  =   os.getenv(f"IBASE_{i}_NAME") or os.getenv(f"IBASE_{i}")
                if not ibase_name:
                    break
                
                ibase_jr                                    =   os.getenv(f"IBASE_{i}_JR")
                ibase_format                                =   os.getenv(f"IBASE_{i}_FORMAT", "lgf")

                if ibase_name and ibase_jr:
                     ibase_info                          =   {
                            g.nms.ib.name                   :   ibase_name,
                            g.nms.ib.jr_dir                 :   ibase_jr,
                            g.nms.ib.jr_format              :   ibase_format,
                            g.nms.ib.total_size             :   0,
                            g.nms.ib.parsed_size            :   0
                        }
                     g.parser.ibases.append(ibase_info)
                     t.debug_print(f"✓ База #{i} загружена: {ibase_name}, формат: {ibase_format}, журнал: {ibase_jr}")
                i                                           +=  1
            
            if len(g.parser.ibases) == 0:
                t.debug_print("⚠ ВНИМАНИЕ: Не найдено ни одной базы данных 1С в переменных окружения!")
                t.debug_print("   Проверьте наличие переменных IBASE_0, IBASE_0_JR и т.д. в файле .env")
            else:
                t.debug_print(f"Всего загружено баз: {len(g.parser.ibases)}")
        except Exception as e:
             t.debug_print(f"✗ Ошибка загрузки баз из переменных окружения: {e}")

        # config.read(g.conf.filename, encoding="UTF8") - no longer needed
        try:
            pass
            # ~~~~~~~ загружаю специфику 1С ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # try:
            #     c1i_exists                                  =   config[g.conf.c1.section_name]["ibase_0"]               # пытаюсь вынть первое значение
            #     i                                           =   0
            #     while c1i_exists:
            #         try:
            #             ibase_info                          =   {
            #                 g.nms.ib.name                   :   config[g.conf.c1.section_name][f"ibase_{str(i)}"],
            #                 g.nms.ib.jr_dir                 :   config[g.conf.c1.section_name][f"ibase_{str(i)}_jr"],
            #                 g.nms.ib.jr_format              :   config[g.conf.c1.section_name]\
            #                                                     [f"ibase_{str(i)}_format"],
            #                 g.nms.ib.total_size             :   0,
            #                 g.nms.ib.parsed_size            :   0
            #             }
            #             g.parser.ibases.append(ibase_info)
            #             i                                   +=  1
            #         except Exception as e:
            #             c1i_exists                          =   False
            #             pass
            # except Exception as e:
            #     t.debug_print("В файле конфигурации нет информационных баз")
            # ~~~~~~~ загружаю специфику ClickHouse ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # try:
            #     g.conf.clickhouse.enabled                   =   strtobool(config[g.conf.clickhouse.section_name]["enabled"])
            #     g.conf.clickhouse.host                      =   config[g.conf.clickhouse.section_name]["host"]
            #     g.conf.clickhouse.port                      =   config[g.conf.clickhouse.section_name]["port"]
            #     g.conf.clickhouse.user                      =   config[g.conf.clickhouse.section_name]["user"]
            #     g.conf.clickhouse.password                  =   config[g.conf.clickhouse.section_name]["password"]
            #     g.conf.clickhouse.database                  =   config[g.conf.clickhouse.section_name]["database"]
            # except:
            #     g.conf.clickhouse.enabled                   =   False

            # ~~~~~~~ загружаю специфику Redis ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # try:
            #     g.conf.redis.enabled                        =   strtobool(config[g.conf.redis.section_name]["enabled"])
            #     g.conf.redis.server_path                    =   config[g.conf.redis.section_name]["server_path"]
            #     g.conf.redis.host                           =   config[g.conf.redis.section_name]["host"]
            #     g.conf.redis.port                           =   config[g.conf.redis.section_name]["port"]
            #     g.conf.redis.db                             =   config[g.conf.redis.section_name]["db"]
            #     g.conf.redis.dir                            =   config[g.conf.redis.section_name]["dir"]
            # except:
            #     g.conf.redis.enabled                        =   False

            # ~~~~~~~ загружаю специфику SOLR ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # try:
            #     g.conf.solr.enabled                         =   strtobool(config[g.conf.solr.section_name]["enabled"])
            # except:
            #     g.conf.solr.enabled                         =   False # По умолчанию выключен

            # g.conf.solr.mem_min                             =   config[g.conf.solr.section_name]["mem_min"]
            # g.conf.solr.mem_max                             =   config[g.conf.solr.section_name]["mem_max"]
            # g.conf.solr.dir                                 =   config[g.conf.solr.section_name]["dir"]
            # g.conf.solr.listen_interface                    =   config[g.conf.solr.section_name]["listen_interface"]
            # g.conf.solr.listen_port                         =   config[g.conf.solr.section_name]["listen_port"]
            # g.conf.solr.solr_host                           =   config[g.conf.solr.section_name]["solr_host"]
            # g.conf.solr.solr_port                           =   config[g.conf.solr.section_name]["solr_port"]
            # g.conf.solr.java_home                           =   config[g.conf.solr.section_name]["java"]
            # g.conf.solr.threads                             =   config[g.conf.solr.section_name]["threads"]

            # ~~~~~~~ загружаю специфику HTTP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # g.conf.http.listen_interface                    =   config[g.conf.http.section_name]["listen_interface"]
            # g.conf.http.listen_port                         =   config[g.conf.http.section_name]["listen_port"]

            # ~~~~~~~ загружаю специфику парсера~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # g.parser.threads                                =   config[g.parser.section_name]["threads"]

            # ~~~~~~~ загружаю специфику отладки~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # try:
            #     g.debug.on                                  =   strtobool(config["debug"]["enabled"])
            #     t.debug_print(f"Debug enabled = {str(g.debug.on)}")
            # except:
            #     pass
            
            # try:
            #     g.debug.on_parser                           =   strtobool(config["debug"]["debug_parser"])
            #     t.debug_print(f"Debug_parser enabled = {str(g.debug.on_parser)}")
            # except:
            #     pass

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        except Exception as e:
            t.debug_print(f"Error while parsing params {str(e)}")
            # t.graceful_shutdown() # Don't kill if config file is missing/bad, we have ENV defaults now
    # ------------------------------------------------------------------------------------------------------------------
    # сохранение конфы (отключено)
    # ------------------------------------------------------------------------------------------------------------------
    def save(fake_param = 0):
        pass
    # ------------------------------------------------------------------------------------------------------------------
    # определение настроек по умлочанию
    # ------------------------------------------------------------------------------------------------------------------
    def detect(fake_param=0, initial=False):
        # Redis default settings
        g.conf.redis.enabled                            =   t.strtobool(os.getenv("REDIS_ENABLED", "False"))
        g.conf.redis.server_path                        =   os.getenv("REDIS_SERVER_PATH", "")
        g.conf.redis.host                               =   os.getenv("REDIS_HOST", "127.0.0.1")
        g.conf.redis.port                               =   os.getenv("REDIS_PORT", "6379")
        g.conf.redis.db                                 =   os.getenv("REDIS_DB", "0")
        g.conf.redis.dir                                =   os.getenv("REDIS_DIR", os.path.join(g.execution.self_dir, "redis_data"))

        # Solr default settings
        g.conf.solr.enabled                             =   t.strtobool(os.getenv("SOLR_ENABLED", "False"))

        t.debug_print("Conf detection")
        d_found                                             =   False
        if is_windows:
        # ~~~~~~~ получение первой активной службы 1C ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for service in psutil.win_service_iter():
                try:
                    d_service                               =   (psutil.win_service_get(service.name())).as_dict()
                except Exception as e:
                    t.debug_print(f"failed to parse {str(service)}",'detect')
                if g.rexp.service_is_1c.search(d_service["binpath"]) and d_service["start_type"] == 'automatic':
                    t.debug_print(f"found {d_service['binpath']}")
                    d_found                                 =   True
                    try:
                        #g.conf.c1.srvinfo                  =   g.rexp.service_1c_workdir.findall(service.binpath())[0]   #берем только первое значение
                        detect_srvinfos                     =   g.rexp.service_1c_workdir.findall(service.binpath())
                        if not len(detect_srvinfos)>0 :
                            t.debug_print("can't detect srvinfo")
                            t.graceful_shutdown(1)
                        srv_dir                             =   re.sub(r'\\\\\\','\\\\' ,detect_srvinfos[0])
                        thread_name                         =   g.threads.config_updater.name \
                                                                    if g.threads.config_updater \
                                                                    else "initial configuration detection"
                        t.debug_print(f"processing {srv_dir}", thread_name)
                        conf.detect2(initial2=initial, d2_srvinfo=srv_dir)
                    except Exception as e:
                        t.debug_print(f"Exception srv_1c {str(e)}")
        else:
            try:
                # Получение списка всех включённых служб
                services_output                             =   subprocess.check_output(
                                                                    ['systemctl', 'list-unit-files'], #, '--all'] , #'--type=service', '--state=enabled'],
                                                                    text=True
                                                                )

                # Разбор вывода команды
                for line in services_output.splitlines():
                    if d_found:
                        break
                    parts                                   =   line.split()
                    #print(parts)
                    if len(parts) < 2:
                        continue  # Пропустить строки, которые не соответствуют формату

                    unit_name, state                        =   parts[0], parts[1]

                    # Проверка, относится ли служба к 1C
                    if g.rexp.daemon_1c.search(unit_name):
                        try:
                            # Получение полной информации о службе
                            d_found                         =   True
                            service_info                    =   subprocess.check_output(
                                                                    ['systemctl', 'show', unit_name],
                                                                    text=True
                                                                )

                            # Извлечение ExecStart из информации о службе
                            iter                            =   0
                            exec_start                      =   ""
                            for info_line in service_info.splitlines():
                                t.debug_print(info_line)
                                if info_line.startswith('ExecStart='):
                                    exec_start              =   info_line[len('ExecStart='):].strip()
                                    iter                    +=  1
                                if info_line.startswith('Environment='):
                                    environment             =   info_line[len('Environment='):].strip()
                                    iter                    +=  1                                
                                if iter == 2:
                                    break
                            
                            c1_data_dir                     =   g.rexp.service_1c_workdir.findall(exec_start)[0]
                            envs                            =   g.rexp.enviroments.findall(environment)
                            environments                    =   {}
                            for token in envs:
                                key                         =   token[0]
                                value                       =   token[1]
                                environments[key]           =   value

                            #t.debug_print(environments)
                            if environments.get(c1_data_dir):
                                c1_data_dir                 =   environments[c1_data_dir]
                            
                            if not os.path.exists(c1_data_dir):
                                t.debug_print(f"Каталог {c1_data_dir} не существует")
                                continue  # Пропустить, если каталог не существует
                            if not exec_start:
                                t.debug_print(f"ExecStart не найден для службы {unit_name}")
                                continue  # Пропустить, если ExecStart не найден

                            # Извлечение srv_dir с помощью регулярного выражения
                            detect_srvinfos                 =   g.rexp.service_1c_workdir.findall(exec_start)
                            if not detect_srvinfos:
                                t.debug_print("can't detect srvinfo")
                                t.graceful_shutdown(1)
                            if len(detect_srvinfos) == 0:
                                t.debug_print("can't detect srvinfo")
                                t.graceful_shutdown(1)
                            srvinfo                         =   detect_srvinfos[0]
                            if environments.get(srvinfo):
                                srvinfo                     =   environments[srvinfo]
                            

                            srv_dir                         =   re.sub(r'\\\\\\', '\\\\', srvinfo)
                            thread_name                     =   g.threads.config_updater.name if g.threads.config_updater else "initial configuration detection"
                            t.debug_print(f"processing {srv_dir}", thread_name)
                            conf.detect2(initial2=initial, d2_srvinfo=srv_dir)
                        except Exception as e:
                            t.debug_print(f"Не удалось проверить статус службы {unit_name}: {e}", 'detect')
            except Exception as e:
                t.debug_print(f"Exception while processing Linux services: {str(e)}")
        if not d_found:
            if not (os.path.exists(g.conf.filename)):
                t.debug_print("1C services not found, conf detection failed")
                t.graceful_shutdown(1)
    # ~~~~~~~ получение списка баз и кластеров 1C ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def detect2(fake_param=0,initial2=False,d2_srvinfo=""):
        regs                                                =   [element for element
                                                                    in os.listdir(d2_srvinfo)
                                                                        if os.path.isdir(os.path.join(d2_srvinfo, element))
                                                                            and g.rexp.is_1c_cluster.findall(element)
                                                                ]                                                       # получаю списков все кластеров
        local_bases_array                                   =   []
        t.debug_print(f"regs={str(regs)}")
        for reg in regs:
            clstr_dir                                       =   os.path.join(d2_srvinfo, reg)
            t.debug_print(f"clstr_dir={str(clstr_dir)}")
            clstr_file                                      =   os.path.join(clstr_dir, g.conf.c1.cluster_file)
            clstr_file_o                                    =   os.path.join(clstr_dir, g.conf.c1.cluster_file_o)
            clstr_file_o                                    =   clstr_file_o if os.path.exists(clstr_file_o) \
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
                t.debug_print(f"no cluster file found with {str(clstr_file)}")
                return
            else:
                t.debug_print(f"processing {str(clstr_file)}")
            clstr_handle                                    =   open(clstr_file, 'r', encoding='UTF8')
            clstr_text                                      =   clstr_handle.read()
            clstr_handle.close()
            bases                                           =   g.rexp.clst_1c_base_rec.findall(clstr_text)
            t.debug_print(f"found clusters={str(bases)}")
            for base in bases:
                ibase_dir                                   =   os.path.join(clstr_dir, base[0])
                ibase_jr_dir                                =   os.path.join(ibase_dir, g.conf.c1.jr_dir)
                ibase_jr_dir                                =   re.sub(r'\\\\\\', '\\\\' ,ibase_jr_dir)                 # https://github.com/WonderMr/Journal2Ct/issues/38
                if(os.path.exists(ibase_jr_dir)):                                                                       # каталог журнала регистрации есть
                    ibase_jr_new_fname                      =   os.path.join(ibase_jr_dir, g.conf.c1.jr_new_fname)      # имя файла нового формата жр
                    ibase_jr_new                            =   os.path.exists(ibase_jr_new_fname)
                    ibase_jr_old_dict_fname                 =   os.path.join(ibase_jr_dir, g.conf.c1.jr_old_dict_fname) # имя файла словаря старого формата жр
                    ibase_jr_old                            =   os.path.exists(ibase_jr_old_dict_fname)                 # если ли файл словаря старого формата ЖР
                    if(ibase_jr_new or ibase_jr_old):
                        ib_nm                               =   t.normalize_ib_name(base[1].upper())
                        ibase_info                          =   {
                            g.nms.ib.name                   :   ib_nm,
                            g.nms.ib.jr_dir                 :   ibase_jr_dir,
                            g.nms.ib.jr_format              :   g.nms.ib.jr_format_new
                                                                if ibase_jr_new else
                                                                g.nms.ib.jr_format_old,
                            'total_size'                    :   0,
                            'parsed_size'                   :   0
                        }                                                                                               # формирую dictionary с информацией о базе
                        
                        # Проверяем, есть ли уже такая база в списке (с блокировкой для thread-safety)
                        base_found                          =   False
                        with g.ibases_lock:
                            for base in g.parser.ibases:
                                if base[g.nms.ib.name]      ==  ibase_info[g.nms.ib.name]:
                                    base_found              =   True
                                    break
                            
                            # Добавляем базу если её ещё нет
                            if not base_found:
                                t.debug_print(f"Обнаружена новая ИБ: {ibase_info[g.nms.ib.name]} → {ibase_info[g.nms.ib.jr_dir]}")
                                g.parser.ibases.append(ibase_info)
                        
                        # Для отслеживания удалённых баз (только при периодическом обновлении)
                        if not initial2:
                            local_bases_array.append(ibase_info)

        if not initial2:                                                                                                # проверяю базы на удалённые
            # Работа с g.parser.ibases защищена блокировкой для thread-safety
            with g.ibases_lock:
                bases_copy                                  =   g.parser.ibases.copy()                                  # из этой копии будем удалять базы
                for each_base in local_bases_array:                                                                     # по всем базам из файла
                    for each_each_base in bases_copy:                                                                   # по всем из копии конфы
                        if each_base[g.nms.ib.name]         ==  each_each_base[g.nms.ib.name]:                          # если есть, то убираем из копии. Уйти должны все существующие
                            bases_copy.remove(each_each_base)
                for each_base in bases_copy:                                                                            # а вот оставшиеся - это удалённые
                    if d2_srvinfo in str(each_base[g.nms.ib.jr_dir]):                                                   # удаляем только базы этого кластера
                        t.debug_print(f"База {each_base[g.nms.ib.name]} удалена из кластера")
                        g.parser.ibases.remove(each_base)
        # ~~~~~~~ установка параметров solr по умолчанию для первого детекта ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if initial2:
            g.conf.solr.mem_min                             =   "2g"
            g.conf.solr.mem_max                             =   "32g"
            g.conf.solr.dir                                 =   os.path.join(g.execution.self_dir, "solr")
            g.conf.solr.listen_interface                    =   "127.0.0.1"
            g.conf.solr.listen_port                         =   "8983"
            g.conf.solr.solr_host                           =   "127.0.0.1"                                             # socket.gethostbyaddr(g.conf.solr.listen_interface)
            g.conf.solr.solr_port                           =   "8983"
            g.conf.solr.java_home                           =   os.path.join(g.execution.self_dir, "java")
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
    # каталог с исполняемым файлом
    g.execution.self_dir                                    =   g.rexp.any_filename.sub('' ,   g.execution.self_name)
    self_full_name_without_ext                              =   g.rexp.any_file_ext.sub('' ,   g.execution.self_name)

    g.conf.filename                                         =   self_full_name_without_ext + "ini"                     # имя файла конфигурации 2019.11.24 Я поймал какой-то странный глюк - двоится при замене. Поэтому сделал так
    
    self_name_without_ext                                   =   g.rexp.any_file_ext.sub('' ,   g.rexp.any_filename.search(g.conf.filename)[0])

    g.debug.dir                                             =   os.path.join(g.execution.self_dir, 'debug')            # каталог для хранения данных отладки
    
    g_debug_filename                                        =   self_name_without_ext  + str(os.getpid())  + '.log'
    g.debug.filename                                        =   os.path.join(g.debug.dir, g_debug_filename)

    #g.parser.state_file                                     =   os.path.join(g.execution.self_dir, "parser.state")     # здесь в json хранятся статусы парсинга файлов
# ======================================================================================================================
# дополнительная инициализация после загрузки/определения параметров
# ======================================================================================================================
def post_init_vars():
    g.execution.solr.url_main                               =   f"http://{g.conf.solr.solr_host}:{g.conf.solr.solr_port}/solr"
    
    # Проверяем соединение с ClickHouse если он включен
    if g.conf.clickhouse.enabled:
        try:
            from clickhouse_driver import Client
            t.debug_print("Проверка соединения с ClickHouse...")
            
            client                                          =   Client(
                                                                    host        =   g.conf.clickhouse.host,
                                                                    port        =   g.conf.clickhouse.port,
                                                                    user        =   g.conf.clickhouse.user,
                                                                    password    =   g.conf.clickhouse.password,
                                                                    database    =   g.conf.clickhouse.database
                                                                )
            
            # Пробуем выполнить простой запрос
            result                                          =   client.execute('SELECT 1')
            
            if result:
                g.stats.clickhouse_connection_ok            =   True
                from datetime import datetime
                g.stats.clickhouse_last_success_time        =   datetime.now()
                t.debug_print(f"✓ ClickHouse подключен: {g.conf.clickhouse.host}:{g.conf.clickhouse.port}/{g.conf.clickhouse.database}")
            else:
                g.stats.clickhouse_connection_ok            =   False
                t.debug_print(f"✗ ClickHouse не ответил корректно")
                
        except Exception as e:
            g.stats.clickhouse_connection_ok                =   False
            from datetime import datetime
            g.stats.clickhouse_last_error_time              =   datetime.now()
            g.stats.clickhouse_last_error_msg               =   str(e)
            g.stats.clickhouse_total_errors                 +=  1
            t.debug_print(f"✗ Ошибка подключения к ClickHouse: {str(e)}")
    else:
        t.debug_print("ClickHouse отключен в конфигурации")
# ======================================================================================================================
# запускает все потоки парсинга, solr и веб-сервер
# ======================================================================================================================
def start_all(wait=False):
    try:
        t.status_print("Инициализация сервиса...")
        t.debug_print("Starting all threads")
        
        # Инициализируем время старта
        from datetime import datetime
        g.stats.start_time                                  =   datetime.now()
        t.debug_print(f"Время запуска службы: {g.stats.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Вывод конфигурации
        g.print_config()
        
        # ~~~~~~~ загружаю или создаю конфигурацию ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        t.debug_print("Load configuration (ENV)")
        conf.load()
        
        # Валидация и очистка баз из ENV
        valid_ibases                                        =   []
        for ibase in g.parser.ibases:
            jr_path                                         =   ibase[g.nms.ib.jr_dir]
            if os.path.exists(jr_path):
                valid_ibases.append(ibase)
                t.debug_print(f"✓ База из ENV: {ibase[g.nms.ib.name]} → {jr_path}")
            else:
                t.debug_print(f"✗ База из ENV удалена (путь не существует): {ibase[g.nms.ib.name]} → {jr_path}")
        
        g.parser.ibases                                     =   valid_ibases
        t.debug_print(f"Валидных баз из ENV: {len(g.parser.ibases)}")
        
        # Запускаем автодетект если указан корневой путь
        if g.conf.c1.srvinfo and os.path.exists(g.conf.c1.srvinfo):
            t.debug_print(f"Запуск автодетекта из корневого пути: {g.conf.c1.srvinfo}")
            conf.detect2(initial2=False, d2_srvinfo=g.conf.c1.srvinfo)
            t.debug_print(f"После автодетекта: {len(g.parser.ibases)} баз")
        elif g.conf.c1.srvinfo:
            t.debug_print(f"⚠ Корневой путь указан, но не существует: {g.conf.c1.srvinfo}")
        else:
            t.debug_print("Корневой путь (C1_SRVINFO_PATH) не указан, автодетект пропущен")
        
        # Если нет ни баз из ENV, ни автодетекта - пытаемся найти службу
        if len(g.parser.ibases) == 0:
            t.debug_print("Базы не найдены, пытаемся найти службу 1С...")
            conf.detect(initial=True)  # initial=True только для настроек Solr по умолчанию
            t.debug_print(f"После поиска службы 1С: {len(g.parser.ibases)} баз")
        
        if len(g.parser.ibases) == 0:
            t.debug_print("═" * 80)
            t.debug_print("⚠ ВНИМАНИЕ: Не найдено ни одной базы данных 1С!")
            t.debug_print("═" * 80)
            t.debug_print("Возможные решения:")
            t.debug_print("  1. Укажите базы в .env:")
            t.debug_print("     IBASE_0=ИмяБазы")
            t.debug_print("     IBASE_0_JR=/путь/к/журналу/1Cv8Log")
            t.debug_print("     IBASE_0_FORMAT=lgf")
            t.debug_print("")
            t.debug_print("  2. Укажите корневой путь для автодетекта:")
            t.debug_print("     C1_SRVINFO_PATH=/home/usr1cv8/.1cv8/1C/1cv8")
            t.debug_print("═" * 80)
        
        # if(os.path.exists(g.conf.filename)):
        #     t.debug_print("Load configuration")
        #     conf.load()
        # else:
        #     t.debug_print("Configuration detection")
        #     conf.detect(initial=True)
        #     conf.save()
        post_init_vars()
        # ~~~~~~~ запускаю cherrypy в фоне ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.cherry                                    =   c.cherry_thread("my little cherry")
        g.threads.cherry.start()
        # ~~~~~~~ запускаю solr в фоне ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if g.conf.solr.enabled:
            g.threads.solr                                      =   s.solr_thread("my pretty solr thread")
            g.threads.solr.start()
        # ~~~~~~~ запускаю redis в фоне ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.redis                                     =   rm.redis_thread("Redis Manager")
        g.threads.redis.start()
        # ~~~~~~~ запускаю sender в фоне ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.sender                                    =   snd.sender_thread("Data Sender")
        g.threads.sender.start()

        # ~~~~~~~ до парсера надо дёрнуть словари ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if len(g.parser.ibases) > 0:
            t.debug_print(f"Reading dictionaries for {len(g.parser.ibases)} bases...")
            for ib in g.parser.ibases:
                t.debug_print(f"Reading dictionary for {ib['ibase_name']}...")
                d.read_ib_dictionary(ib['ibase_name'])
                t.debug_print(f"✓ Dictionary for {ib['ibase_name']} loaded")
        # ~~~~~~~ создаю и запускаю потоки парсеров ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.threads.parser                                    =   p.parser("lgp")
        g.threads.parser.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~ создаю и запускаю потоки парсеров для нового формата ЖР ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        #g.threads.parser_new                                =   p.parser("lgd")
        #g.threads.parser_new.start(); # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        t.debug_print("✓ SERVICE STARTED AND READY")
        t.status_print("Сервис успешно запущен. Ожидание событий...")
        
        # Вывод конфигурации в консоль
        t.status_print("=" * 60)
        t.status_print("ТЕКУЩАЯ КОНФИГУРАЦИЯ:")
        t.status_print(f"• ClickHouse: {'ВКЛ' if g.conf.clickhouse.enabled else 'ВЫКЛ'}")
        t.status_print(f"• Redis:      {'ВКЛ' if g.conf.redis.enabled else 'ВЫКЛ'}")
        t.status_print(f"• Solr:       {'ВКЛ' if g.conf.solr.enabled else 'ВЫКЛ'}")
        t.status_print(f"• Debug:      {'ВКЛ' if g.debug.on else 'ВЫКЛ'}")
        t.status_print(f"• Баз 1С:     {len(g.parser.ibases)}")
        t.status_print("=" * 60)
        
        if not g.debug.on:
            t.status_print("ВНИМАНИЕ: Режим отладки выключен. Подробные логи скрыты.")
            t.status_print("Статистика будет выводиться каждую минуту.")

        last_stats_time                                     =   time.time()
        
        while wait:
            # Heartbeat каждую минуту
            current_time                                    =   time.time()
            if current_time - last_stats_time >= 60:
                uptime                                      =   datetime.now() - g.stats.start_time
                uptime_str                                  =   str(uptime).split('.')[0] # убираем микросекунды
                
                stats_parts                                 =   []
                stats_parts.append(f"HEARTBEAT | Uptime: {uptime_str}")
                stats_parts.append(f"Баз: {len(g.parser.ibases)}")
                stats_parts.append(f"Записей: {g.stats.total_records_parsed}")
                
                if g.conf.clickhouse.enabled:
                    stats_parts.append(f"CH: {g.stats.clickhouse_total_sent}/{g.stats.clickhouse_total_errors}")
                    
                if g.conf.solr.enabled:
                    stats_parts.append(f"Solr: {g.stats.solr_total_sent}/{g.stats.solr_total_errors}")
                    
                if g.conf.redis.enabled:
                    stats_parts.append(f"Redis: {g.stats.redis_total_queued}/{g.stats.redis_total_errors}")
                
                t.status_print(" | ".join(stats_parts))
                    
                last_stats_time                             =   current_time
                
            time.sleep(g.waits.in_cycle_we_trust)
    except Exception as e:
        t.debug_print(f"Exception3 {str(e)}")
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
                
                # Проверяем базы из ENV на существование (с блокировкой)
                with g.ibases_lock:
                    valid_ibases                            =   []
                    for ibase in g.parser.ibases[:]:  # копия списка
                        if os.path.exists(ibase[g.nms.ib.jr_dir]):
                            valid_ibases.append(ibase)
                        else:
                            t.debug_print(f"База {ibase[g.nms.ib.name]} удалена (журнал недоступен)", "IB monitor")
                    
                    g.parser.ibases                         =   valid_ibases
                
                # Запускаем автодетект если указан корневой путь (с блокировкой)
                if g.conf.c1.srvinfo and os.path.exists(g.conf.c1.srvinfo):
                    with g.ibases_lock:
                        conf.detect2(initial2=False, d2_srvinfo=g.conf.c1.srvinfo)
                
            except Exception as e:
                t.debug_print(f"Exception on config update. Error is {str(e)}", "IB monitor")
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
                            t.debug_print(f"warming {i_base[g.nms.ib.name]} cache",self.name)
                            r.full_proceess_read(f"ref={i_base[g.nms.ib.name]}&КоличествоСобытий=1")
                time.sleep(g.waits.warming_cache_wait)
            except Exception as e:
                t.debug_print(f"Exception while warming cache. Error is {str(e)}",self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        self.run                                            =   False
# ======================================================================================================================
# останавливает все потоки парсинга, solr и web-server
# ======================================================================================================================
def stop_all():
    try:
        t.debug_print("Останавливаем все потоки...")
        
        # ~~~~~~~ останавливаю solr ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'solr') and g.threads.solr: 
            t.debug_print("Останавливаем Solr...")
            g.threads.solr.stop()
            
        # ~~~~~~~ останавливаю redis ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'redis') and g.threads.redis: 
            t.debug_print("Останавливаем Redis...")
            g.threads.redis.stop()
            
        # ~~~~~~~ останавливаю sender ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'sender') and g.threads.sender: 
            t.debug_print("Останавливаем Sender...")
            g.threads.sender.stop()
            
        # ~~~~~~~ останавливаю cherrypy ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'cherry') and g.threads.cherry:
            t.debug_print("Останавливаем CherryPy...")
            g.threads.cherry.stop()
            
        # ~~~~~~~ останавливаю потоки парсера ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'parser') and g.threads.parser:
            t.debug_print("Останавливаем Parser...")
            g.threads.parser.stop()
            
        # ~~~~~~~ останавливаю обновлятель списка баз ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'config_updater') and g.threads.config_updater:
            t.debug_print("Останавливаем Config Updater...")
            g.threads.config_updater.stop()
            
        # ~~~~~~~ останавливаю подогреватель кэша ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if hasattr(g.threads, 'warming_cache') and g.threads.warming_cache:
            t.debug_print("Останавливаем Warming Cache...")
            g.threads.warming_cache.stop()
            
        t.debug_print("✓ Все потоки остановлены")
    except Exception as e:
        t.debug_print(f"⚠ Исключение при остановке потоков: {str(e)}")
# ======================================================================================================================
# Go
# ======================================================================================================================
def main():
    init_vars()
    # ==================================================================================================================
    # Проверка прав доступа (Linux)
    # ==================================================================================================================
    if not is_windows:
        try:
            # Проверяем запись в директорию
            test_dir                                        =   g.execution.self_dir
            if os.path.exists(g.debug.dir):
                test_dir                                    =   g.debug.dir
            
            if not os.access(test_dir, os.W_OK):
                import pwd, grp
                current_uid                                 =   os.getuid()
                try:
                    current_user                            =   pwd.getpwuid(current_uid).pw_name
                except:
                    current_user                            =   str(current_uid)
                
                # Пытаемся определить правильную группу (grp1cv8 или текущая)
                target_group                                =   "grp1cv8"
                try:
                    grp.getgrnam(target_group)
                except KeyError:
                    # Если группы grp1cv8 нет, предлагаем группу пользователя
                    try:
                        target_group                        =   grp.getgrgid(os.getgid()).gr_name
                    except:
                        target_group                        =   current_user

                print("="*80)
                print(f"!!! ОШИБКА ДОСТУПА (PERMISSION DENIED) !!!")
                print(f"Сервис не может писать в каталог: {test_dir}")
                print(f"Запущен от пользователя:          {current_user} (uid={current_uid})")
                try:
                    stat_info                               =   os.stat(test_dir)
                    print(f"Владелец каталога:                {stat_info.st_uid}:{stat_info.st_gid}")
                    print(f"Права на каталог:                 {oct(stat_info.st_mode)[-3:]}")
                except:
                    pass
                print("-" * 80)
                print("ЧТОБЫ ИСПРАВИТЬ, ВЫПОЛНИТЕ КОМАНДУ:")
                print(f"sudo chown -R {current_user}:{target_group} {g.execution.self_dir}")
                print("="*80)
                sys.exit(77)                                                                                            # EX_NOPERM
        except ImportError:
            pass
        except SystemExit:
            raise
        except Exception as e:
            print(f"Ошибка при проверке прав: {e}")
    # ==================================================================================================================
    
    if ('console' in sys.argv):
        g.execution.running_in_console                  =   True
        print(f"Запуск в консольном режиме. Debug enabled: {g.debug.on}")
        start_all(wait = True)
    elif is_windows:
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
            servicemanager.PrepareToHostSingle(nikita_service)
            # Now ask the service manager to fire things up for us...
            servicemanager.StartServiceCtrlDispatcher()
            print("service done!")
        elif "--version" in sys.argv:
            print("Nikita Service 1.0.0")
            sys.exit(0)
        else:
            win32serviceutil.HandleCommandLine(nikita_service)
    else:
        g.execution.running_in_console                  =   True
        start_all(wait = True)

if __name__ ==  '__main__':
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        t.debug_print("Something went bad!")
        import traceback

        traceback.print_exc()
# ======================================================================================================================