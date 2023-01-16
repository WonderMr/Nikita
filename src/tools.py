# -*- coding: utf-8 -*-
import  win32event
import  os
import  datetime
import  servicemanager
import  sqlite3
import  json
import  urllib
import  time
# ======================================================================================================================
from    src                 import  globals                 as  g
# ======================================================================================================================
# ----------------------------------------------------------------------------------------------------------------------
# разные используемый функции
# ----------------------------------------------------------------------------------------------------------------------
class tools():
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # жёсткое завершение процесса через taskkill
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def seppuku(s_code = 0):
        tools.debug_print("Exit program with code = " + str(s_code))
        if not g.execution.running_in_console:
            tools.debug_print("Stopping service")
            win32event.SetEvent(win32event.CreateEvent(None, 0, 0, None))
        else:
            from subprocess import call
            # Я пока не научился хорошо и корректно завершать свой процесс, поэтому просто занимаюсь самоубийством
            sys32                                           =   os.path.expandvars("%SystemRoot%")+'\\system32\\'
            cmd                                             =   sys32+"cmd.exe"
            taskkill                                        =   sys32+"taskkill.exe"
            temp                                            =   os.path.expandvars("%temp%")+'\\suicide.cmd'
            suicide                                         =   open(temp,'w')
            print(taskkill+" /f /pid "+str(os.getpid()))
            suicide.write(taskkill+" /f /pid "+str(os.getpid()))
            suicide.close()
            murder                                          =  cmd+" /c "+temp
            print(str([cmd,'/c',temp]))
            call([cmd,'/c',temp])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # печать отладочного сообщения, работает только на взведённом глобально флаге отладки
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def debug_print(dp_msg,dp_thread=""):
        if (g.debug.on):
            dp_dt                                           =   datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            dp_msg                                          =   dp_dt + ":::" + dp_thread + ":::" + dp_msg
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if g.execution.running_in_console:
                print(dp_msg)
            #else:
            #    servicemanager.LogErrorMsg(dp_msg)
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            if(g.debug.filehandle):                                                                                     # если уже открыт
                g.debug.filehandle.write(dp_msg + "\n")
                g.debug.filehandle.flush()
            else:                                                                                                       # если ещё не открыт
                if(not os.path.exists(g.debug.dir)):
                    os.makedirs(g.debug.dir)
                g.debug.filehandle                          =   open(g.debug.filename, 'a', encoding='UTF8')
                g.debug.filehandle.write(dp_msg + "\n")
                g.debug.filehandle.flush()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # чтение файла и возврат содержимого
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def readfile(r_filename,encoding='UTF8'):
        if(os.path.exists(r_filename)):
            rf_handle                                       =   open(r_filename, 'r', encoding=encoding)
            rf_content                                      =   rf_handle.read()
            rf_handle.close()
            return rf_content
        else:
            return ""
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # выполняет командру SQlite3 и возвращает результат
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def sqlite3_exec(sql3_file,sql3_cmd):
        ret                                                 =   None
        if(os.path.exists(sql3_file)):
            try:
                sql                                         =   sqlite3.connect(sql3_file).cursor()
                sql.execute('''PRAGMA encoding = "UTF-8";''')
                ret                                         =   sql.execute(sql3_cmd).fetchall()
            except Exception as e:
                tools.debug_print("Exception while sqlexec "+sql3_cmd + " on file "+sql3_file + " error is " + str(e))
            finally:
                sql.close()
        return ret
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # смещение часового пояса
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_time_zone(self                                  =   None):
        d                                                   =   datetime.datetime
        t                                                   =   int(d.timestamp(d.now()))                               # фиксирую время в epoch
        u                                                   =   int(d.utcfromtimestamp(t).timestamp())
        tz                                                  =   t - u
        return str(tz // 60)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 2019.01.11 17:00 всё таки надо имя править
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def normalize_ib_name(n_ib_name):
        n_ib_name                                           =   urllib.parse.quote(n_ib_name)
        n_ib_name                                           =   n_ib_name.replace("%","aAa_")
        return n_ib_name
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 2019.01.28 16:30 всё таки надо имя править
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def denormalize_ib_name(dn_ib_name):
        dn_ib_name                                          =   dn_ib_name.replace("aAa_","%")
        return urllib.parse.unquote(dn_ib_name)
    # ------------------------------------------------------------------------------------------------------------------
    # получение количества записей lgd-файла
    # ------------------------------------------------------------------------------------------------------------------
    def get_lgd_evens_count(dlr_name):
        dlr_ret                                             =   [0,0]
        try:
            max_row_q                                       =   tools.sqlite3_exec(
                                                                    dlr_name,
                                                                    g.parser.lgd_select_last_id
                                                                )
            min_row_q                                       =   tools.sqlite3_exec(
                                                                    dlr_name,
                                                                    g.parser.lgd_select_first_id
                                                                )
            if (isinstance(max_row_q, list) and isinstance(min_row_q, list)):                                           # если всё норм
                dlr_ret                                     =   [max_row_q[0][0],min_row_q[0][0]]
        except Exception as e:  # здесь споткнулся на битых файлах
            tools.debug_print("Exception on query lgd " + str(e))
        return dlr_ret
    # ------------------------------------------------------------------------------------------------------------------
    # запись сообщения об ошибке авторизации
    # ------------------------------------------------------------------------------------------------------------------
    def log_msg(dp_msg):
        g.notify.filename                                   =   g.execution.self_dir+"\\log_msg.txt"
        dp_dt                                               =   datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        dp_msg                                              =   dp_dt + ":::" + dp_msg
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if(g.notify.filehandle):                                                                                        # если уже открыт
            g.notify.filehandle.write(dp_msg + "\n")
            g.notify.filehandle.flush()
        else:                                                                                                           # если ещё не открыт
            g.notify.filehandle                             =   open(g.notify.filename,'a',encoding='UTF8')
            g.notify.filehandle.write(dp_msg + "\n")
            g.notify.filehandle.flush()
    # ------------------------------------------------------------------------------------------------------------------
    # Получение имени файла по ID
    # ------------------------------------------------------------------------------------------------------------------
    def get_file_by_id(gfbi_id):
        try:
            gfbi_ret                                        =   tools.read_cache_id(rci_id=gfbi_id)
            if not gfbi_ret:
                tools.read_ids_file()
                gfbi_ret                                    =   tools.read_cache_id(rci_id=gfbi_id)
        except Exception as e:
            tools.debug_print("get_file_by_id got Exception" + str(e))
            return False
        return gfbi_ret
    # ------------------------------------------------------------------------------------------------------------------
    # Получение ID от имени файла
    # ------------------------------------------------------------------------------------------------------------------
    def get_file_id_by_name(gfibn_name):
        try:
            gfibn_ret                                       =   tools.read_cache_id(rci_filename=gfibn_name)
            if not gfibn_ret:
                tools.read_ids_file()
                gfibn_ret                                   =   tools.read_cache_id(rci_filename=gfibn_name)
                if not gfibn_ret:                                                                                       # надо делать новый ID
                    g.parser.solr_id_file_lock              =   True
                    gfibn_max                               =   1
                    for gfibn_elem in g.cache.file_ids:
                        if gfibn_elem["id"]                 >   gfibn_max:                                              # опередеялю последнее значение
                            gfibn_max                       =   gfibn_elem["id"]
                        gfibn_max                           +=  1
                    gfibn_local                             =   {}
                    gfibn_local["id"]                       =   gfibn_max
                    gfibn_local["filename"]                 =   gfibn_name
                    gfibn_ret                               =   gfibn_max
                    g.cache.file_ids.append(gfibn_local)
                    gfibn_handle                            =   open(g.parser.solr_id_file, 'w', encoding='UTF8')       # перезаписываю
                    json.dump(g.cache.file_ids, gfibn_handle, indent=2)
                    gfibn_handle.close()

        except Exception as e:
            tools.debug_print("get_file_by_id got Exception" + str(e))
        finally:
            g.parser.solr_id_file_lock                      =   False
        return gfibn_ret
    # ------------------------------------------------------------------------------------------------------------------
    # Читаем id file и заполняем кэш
    # ------------------------------------------------------------------------------------------------------------------
    def read_ids_file():
        try:
            if not os.path.exists(g.parser.solr_id_file):
                return
            while g.parser.solr_id_file_lock:                                                                           # если файл заперт, то ждём
                time.sleep(g.waits.in_cycle_we_trust)
            g.parser.solr_id_file_lock                      =   True
            del g.cache.file_ids[:]                                                                                     # чищу кэш
            rif_handle                                      =   open(g.parser.solr_id_file, 'r', encoding='UTF8')       # открываю файл
            rif_context                                     =   rif_handle.read()                                       # читаем файл
            rif_handle.close()                                                                                          # закрываю хэндл
            rif_json                                        =   json.loads(rif_context)                                 # читаю содержимое
            # заполняем кэш --------------------------------------------------------------------------------------------
            for rif_rec in rif_json:                                                                                    # по всем записям
                rif_local                                   =   {}
                rif_local['filename']                       =   rif_rec['filename']
                rif_local['id']                             =   rif_rec['id']
                g.cache.file_ids.append(rif_local)
        except Exception as e:
            tools.debug_print("read_ids_file got Exception" + str(e))
        finally:
            g.parser.solr_id_file_lock                      =   False

    # ------------------------------------------------------------------------------------------------------------------
    # Получаем нужное значение из кэша id файлов
    # ------------------------------------------------------------------------------------------------------------------
    def read_cache_id(rci_filename="",rci_id=0):
        try:
            if rci_id>0:
                for rci_elem in g.cache.file_ids:
                    if rci_id == rci_elem["id"]:
                        return rci_elem["filename"]
            if rci_filename:
                for rci_elem in g.cache.file_ids:
                    if rci_filename == rci_elem["filename"]:
                        return rci_elem["id"]
        except Exception as e:
            tools.debug_print("read_cache_id got Exception" + str(e))
            return False
        return False
# ======================================================================================================================