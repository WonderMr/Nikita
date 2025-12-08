# -*- coding: utf-8 -*-
import  threading
import  time
import  requests
import  datetime
import  traceback
from    clickhouse_driver   import  Client                  as  ch

from    src.tools           import  tools                   as  t
from    src                 import  globals                 as  g
from    src.redis_manager   import  queue

# ======================================================================================================================
# Утилиты для отправки данных
# ======================================================================================================================

# ----------------------------------------------------------------------------------------------------------------------
# Экранирование спецсимволов для ClickHouse
# ----------------------------------------------------------------------------------------------------------------------
def escape_clickhouse(s: str) -> str:
    return (
        s
        .replace("\\", r"\\")     # обратный слеш
        .replace("'", r"\'")      # одинарная кавычка
        .replace("\n", r"\n")     # переход строки
        .replace("\r", r"\r")     # возврат каретки
    )

# ----------------------------------------------------------------------------------------------------------------------
# Отправка пакета данных в ClickHouse
# ----------------------------------------------------------------------------------------------------------------------
def send_to_clickhouse(chclient, data, base_name, logger_name):
    if not chclient:
        t.debug_print(f"ClickHouse не настроен, пропускаем отправку {len(data)} записей для базы {base_name}", logger_name)
        return True                                                                                                     # Если CH не настроен, считаем отправку успешной
    
    start_time                                              =   time.time()
    
    try:
        t.debug_print(f"→ CLICKHOUSE: Начинаем отправку пакета для базы '{base_name}' (записей: {len(data)})", logger_name)
        
        rows                                                =   []
        for rec in data:
            date_str                                        =   f"{rec['r1'][0:4]}-{rec['r1'][4:6]}-{rec['r1'][6:8]} {rec['r1'][8:10]}:{rec['r1'][10:12]}:{rec['r1'][12:14]}"
            dt                                              =   datetime.datetime.fromisoformat(date_str)
            
            row                                             =   (
                                                                    dt,                                                 # r1 DateTime
                                                                    dt,                                                 # r1a DateTime (дублируем, как в оригинале)
                                                                    rec['r2'],                                          # r2
                                                                    rec['r3'],                                          # r3
                                                                    rec['r3a'],                                         # r3a
                                                                    rec['rr4']['name'],                                 # r4name
                                                                    rec['rr4']['uuid'],                                 # r4guid
                                                                    rec['rr5'],                                         # r5
                                                                    rec['rr6'],                                         # r6
                                                                    int(rec['rr7']),                                    # r7 (теперь Int64)
                                                                    rec['rr8'],                                         # r8
                                                                    rec['rr9'],                                         # r9
                                                                    rec['rr10'],                                        # r10
                                                                    rec['rr11']['name'],                                # r11name
                                                                    rec['rr11']['uuid'],                                # r11guid
                                                                    str(rec['rr12']),                                   # r12
                                                                    str(rec['rr13']),                                   # r13
                                                                    str(rec['rr14']),                                   # r14
                                                                    int(rec['rr15']),                                   # r15
                                                                    int(rec['rr16']),                                   # r16
                                                                    int(rec['rr17']),                                   # r17
                                                                    int(rec['rr18']),                                   # r18
                                                                    int(rec['rr19']),                                   # r19
                                                                    int(rec['id']),                                     # file_id
                                                                    int(rec['pos'])                                     # file_pos
                                                                )
            rows.append(row)
        
        if rows:
            query                                           =   f"INSERT INTO {g.conf.clickhouse.database}.`{base_name}` (r1, r1a, r2, r3, r3a, r4name, r4guid, r5, r6, r7, r8, r9, r10, r11name, r11guid, r12, r13, r14, r15, r16, r17, r18, r19, file_id, file_pos) VALUES"
            exec_result                                     =   chclient.execute(query, rows)
            elapsed_time                                    =   time.time() - start_time
            
            # Обновляем статистику успешной отправки
            g.stats.clickhouse_total_sent                   +=  len(rows)
            g.stats.clickhouse_last_success_time            =   datetime.datetime.now()
            g.stats.clickhouse_connection_ok                =   True
            
            t.debug_print(f"✓ CLICKHOUSE: Успешно отправлено {len(rows)} записей в таблицу {g.conf.clickhouse.database}.{base_name}", logger_name)
            t.debug_print(f"✓ CLICKHOUSE: Время выполнения: {elapsed_time:.3f} сек ({len(rows)/elapsed_time:.1f} записей/сек)", logger_name)
            t.debug_print(f"✓ CLICKHOUSE: Всего отправлено за сессию: {g.stats.clickhouse_total_sent} записей", logger_name)
        return True

    except Exception as e:
        elapsed_time                                        =   time.time() - start_time
        error_msg                                           =   str(e)
        
        # Обновляем статистику ошибок
        g.stats.clickhouse_total_errors                     +=  1
        g.stats.clickhouse_last_error_time                  =   datetime.datetime.now()
        g.stats.clickhouse_last_error_msg                   =   error_msg
        g.stats.clickhouse_connection_ok                    =   False
        
        # Добавляем в список последних ошибок
        error_entry                                         =   (datetime.datetime.now(), "ClickHouse", f"{base_name}: {error_msg}")
        g.stats.last_errors.append(error_entry)
        if len(g.stats.last_errors)                         >   10:
            g.stats.last_errors.pop(0)
        
        t.debug_print(f"✗ CLICKHOUSE: Ошибка отправки в {g.conf.clickhouse.database}.{base_name}: {error_msg}", logger_name)
        t.debug_print(f"✗ CLICKHOUSE: Время до ошибки: {elapsed_time:.3f} сек", logger_name)
        t.debug_print(f"✗ CLICKHOUSE: Всего ошибок за сессию: {g.stats.clickhouse_total_errors}", logger_name)
        t.debug_print(f"✗ CLICKHOUSE: Traceback:\n{traceback.format_exc()}", logger_name)
        return False

# ----------------------------------------------------------------------------------------------------------------------
# Отправка пакета данных в Solr
# ----------------------------------------------------------------------------------------------------------------------
def send_to_solr(url, data, logger_name):
    start_time                                              =   time.time()
    
    try:
        t.debug_print(f"→ SOLR: Отправка пакета на {url} (записей: {len(data)})", logger_name)
        status_code                                         =   requests.post(url=url, json=data).status_code
        elapsed_time                                        =   time.time() - start_time
        
        if status_code                                      ==  200:
            # Обновляем статистику успешной отправки
            g.stats.solr_total_sent                         +=  len(data)
            g.stats.solr_last_success_time                  =   datetime.datetime.now()
            g.stats.solr_connection_ok                      =   True
            
            t.debug_print(f"✓ SOLR: Успешно отправлено {len(data)} записей на {url}", logger_name)
            t.debug_print(f"✓ SOLR: Время выполнения: {elapsed_time:.3f} сек ({len(data)/elapsed_time:.1f} записей/сек)", logger_name)
            t.debug_print(f"✓ SOLR: Всего отправлено за сессию: {g.stats.solr_total_sent} записей", logger_name)
        else:
            # Обновляем статистику ошибок
            g.stats.solr_total_errors                       +=  1
            g.stats.solr_last_error_time                    =   datetime.datetime.now()
            g.stats.solr_last_error_msg                     =   f"HTTP статус: {status_code}"
            g.stats.solr_connection_ok                      =   False
            
            # Добавляем в список последних ошибок
            error_entry                                     =   (datetime.datetime.now(), "Solr", f"HTTP {status_code}: {url}")
            g.stats.last_errors.append(error_entry)
            if len(g.stats.last_errors)                     >   10:
                g.stats.last_errors.pop(0)
            
            t.debug_print(f"✗ SOLR: Ошибка отправки, статус: {status_code}", logger_name)
            t.debug_print(f"✗ SOLR: Всего ошибок за сессию: {g.stats.solr_total_errors}", logger_name)
        
        return status_code
        
    except Exception as e:
        elapsed_time                                        =   time.time() - start_time
        error_msg                                           =   str(e)
        
        # Обновляем статистику ошибок
        g.stats.solr_total_errors                           +=  1
        g.stats.solr_last_error_time                        =   datetime.datetime.now()
        g.stats.solr_last_error_msg                         =   error_msg
        g.stats.solr_connection_ok                          =   False
        
        # Добавляем в список последних ошибок
        error_entry                                         =   (datetime.datetime.now(), "Solr", f"{url}: {error_msg}")
        g.stats.last_errors.append(error_entry)
        if len(g.stats.last_errors)                         >   10:
            g.stats.last_errors.pop(0)
        
        t.debug_print(f"✗ SOLR: Исключение при отправке: {error_msg}", logger_name)
        t.debug_print(f"✗ SOLR: Время до ошибки: {elapsed_time:.3f} сек", logger_name)
        t.debug_print(f"✗ SOLR: Всего ошибок за сессию: {g.stats.solr_total_errors}", logger_name)
        return 500

# ----------------------------------------------------------------------------------------------------------------------
# Универсальная функция отправки (Диспетчер)
# ----------------------------------------------------------------------------------------------------------------------
def post_query(chclient, solr_url, data, base_name, logger_name, bypass_redis=False):
    ret_ok                                                  =   200
    ret_err                                                 =   500
    
    # 1. Если Redis включен и мы не обходим его (т.е. мы не Sender thread)
    if g.conf.redis.enabled and not bypass_redis:
        t.debug_print("→ REDIS: Отправка в очередь Redis...", logger_name)
        
        try:
            if queue.push(data, base_name):
                # Обновляем статистику Redis
                g.stats.redis_total_queued                  +=  len(data)
                g.stats.redis_last_success_time             =   datetime.datetime.now()
                g.stats.redis_connection_ok                 =   True
                
                t.debug_print("✓ REDIS: Успешно помещено в очередь", logger_name)
                return ret_ok
            else:
                # Обновляем статистику ошибок Redis
                g.stats.redis_total_errors                  +=  1
                g.stats.redis_last_error_time               =   datetime.datetime.now()
                g.stats.redis_last_error_msg                =   "Ошибка добавления в очередь"
                g.stats.redis_connection_ok                 =   False
                
                error_entry                                 =   (datetime.datetime.now(), "Redis", "Ошибка добавления в очередь")
                g.stats.last_errors.append(error_entry)
                if len(g.stats.last_errors)                 >   10:
                    g.stats.last_errors.pop(0)
                
                t.debug_print("✗ REDIS: Ошибка, переключение на прямую отправку", logger_name)
        except Exception as e:
            # Обновляем статистику ошибок Redis
            g.stats.redis_total_errors                      +=  1
            g.stats.redis_last_error_time                   =   datetime.datetime.now()
            g.stats.redis_last_error_msg                    =   str(e)
            g.stats.redis_connection_ok                     =   False
            
            error_entry                                     =   (datetime.datetime.now(), "Redis", str(e))
            g.stats.last_errors.append(error_entry)
            if len(g.stats.last_errors)                     >   10:
                g.stats.last_errors.pop(0)
            
            t.debug_print(f"✗ REDIS: Исключение: {str(e)}, переключение на прямую отправку", logger_name)
    
    # 2. Прямая отправка (или если Redis недоступен/обойден)
    success                                                 =   True
    sent_to_any                                             =   False
    
    # ClickHouse
    if g.conf.clickhouse.enabled:
        if send_to_clickhouse(chclient, data, base_name, logger_name):
            sent_to_any                                     =   True
        else:
            success                                         =   False
    
    # Solr (только если включен и URL задан)
    if solr_url and g.conf.solr.enabled:
        solr_status                                         =   send_to_solr(solr_url, data, logger_name)
        if solr_status                                      ==  200:
            sent_to_any                                     =   True
        else:
            success                                         =   False
            t.debug_print(f"✗ Solr: Отправка не удалась (статус: {solr_status})", logger_name)
    
    if not sent_to_any and not g.conf.clickhouse.enabled and not g.conf.solr.enabled:
        t.debug_print("⚠ ВНИМАНИЕ: Ни ClickHouse, ни Solr не настроены! Данные никуда не отправлены.", logger_name)
    
    result                                                  =   ret_ok if success else ret_err
    return result

# ======================================================================================================================
# Поток отправки данных из очереди Redis
# ======================================================================================================================
class sender_thread(threading.Thread):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Инициализация
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name
        self.stop_signal                                    =   False
        self.chclient                                       =   None
        
        if g.conf.clickhouse.enabled:
            try:
                t.debug_print(f"Sender: Подключение к ClickHouse...", self.name)
                self.chclient                               =   ch(
                                                                    host        =   g.conf.clickhouse.host, 
                                                                    port        =   g.conf.clickhouse.port, 
                                                                    user        =   g.conf.clickhouse.user, 
                                                                    password    =   g.conf.clickhouse.password,
                                                                    database    =   g.conf.clickhouse.database
                                                                )
                self.chclient.execute('SELECT 1')
                t.debug_print(f"✓ Sender: ClickHouse подключен", self.name)
            except Exception as e:
                t.debug_print(f"✗ Sender: Ошибка подключения к ClickHouse: {str(e)}", self.name)
                self.chclient                               =   None

        t.debug_print("Thread initialized", self.name)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Основной цикл
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        t.debug_print("Sender thread started", self.name)
        while not self.stop_signal:
            if not g.conf.redis.enabled:
                time.sleep(5)
                continue

            try:
                # Читаем из очереди
                base_name, data                             =   queue.pop(timeout=2)
                
                if base_name and data:
                    t.debug_print(f"Got {len(data)} records for {base_name} from Redis", self.name)
                    
                    solr_url                                =   f"{g.execution.solr.url_main}/{base_name}/update?wt=json"
                    
                    ret_code                                =   post_query(
                                                                    self.chclient,
                                                                    solr_url,
                                                                    data,
                                                                    base_name,
                                                                    self.name,
                                                                    bypass_redis=True
                                                                )
                    
                    if ret_code                             !=  200:
                        t.debug_print(f"Failed to send data (code {ret_code}).", self.name)
                        time.sleep(1)
            except Exception as e:
                t.debug_print(f"Sender loop exception: {str(e)}", self.name)
                time.sleep(1)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Остановка потока
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        self.stop_signal                                    =   True
