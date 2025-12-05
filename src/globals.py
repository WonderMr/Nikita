# -*- coding: utf-8 -*-
import  re
import os
from dotenv import load_dotenv

load_dotenv()

# Функция для вывода конфигурации (вызывается после инициализации tools)
def print_config():
    """Выводит текущую конфигурацию в лог"""
    from src.tools import tools as t
    t.debug_print("=" * 80)
    t.debug_print("ЗАГРУЗКА КОНФИГУРАЦИИ NIKITA")
    t.debug_print("=" * 80)
    t.debug_print(f"CLICKHOUSE_ENABLED: {os.getenv('CLICKHOUSE_ENABLED', 'False')}")
    t.debug_print(f"CLICKHOUSE_HOST: {os.getenv('CLICKHOUSE_HOST', 'localhost')}")
    t.debug_print(f"CLICKHOUSE_PORT: {os.getenv('CLICKHOUSE_PORT', '9000')}")
    t.debug_print(f"CLICKHOUSE_DATABASE: {os.getenv('CLICKHOUSE_DATABASE', 'zhr1c')}")
    t.debug_print(f"CLICKHOUSE_USER: {os.getenv('CLICKHOUSE_USER', 'default')}")
    t.debug_print(f"REDIS_ENABLED: {os.getenv('REDIS_ENABLED', 'False')}")
    t.debug_print(f"SOLR_ENABLED: {os.getenv('SOLR_ENABLED', 'False')}")
    t.debug_print(f"DEBUG_ENABLED: {os.getenv('DEBUG_ENABLED', 'True')}")
    t.debug_print("=" * 80)

# ======================================================================================================================
# в блоке переменных выход за длину разрешён
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
# ======================================================================================================================
# класс описания службы Windows
# ======================================================================================================================
class service:
    name                                                        =   "Journal2Ct"
    display_name                                                =   "2С:Служба быстрого журнала регистрации"
    description                                                 =   "Обеспечивает индексацию и быстрый поиск по " \
                                                                    "журналам регистрации"
# ======================================================================================================================
# переменные времени исполнения программы или потоков
# ======================================================================================================================
class execution:
    running_in_console                                          =   False                                               # признак работы в консоли
    self_name                                                   =   ""                                                  # имя исполняемого файла или скрипта
    self_dir                                                    =   ""                                                  # каталог исполняемого файла или скрипта
    # ==================================================================================================================
    class solr:
        pid                                                     =   0                                                   # Process identifier для java, в котором крутится Solr
        url_main                                                =   ""                                                  # url сервера Solr
        #pysorl                                                  =   None                                                # объект pysolr
        started                                                 =   False                                               # признак того, что Solr проснулся
    # ==================================================================================================================
    class c1_dicts:
        dict_actual_filesizes                                   =   {}                                                  # отдельный словарь для размеров файлов словарей. если размер файла изменился, то словарь перечитываем
        users                                                   =   {}                                                  # словарь пользователей ИБ из словаря старого формата ЖР для конкретной базы
        computers                                               =   {}                                                  # словарь компьютеров из словаря старого формата ЖР для конкретной базы
        applications                                            =   {}                                                  # словарь приложенией из словаря старого формата ЖР для конкретной базы
        actions                                                 =   {}                                                  # словарь событий из словаря старого формата ЖР для конкретной базы
        metadata                                                =   {}                                                  # словарь метаданных из словаря старого формата ЖР для конкретной базы
        servers                                                 =   {}                                                  # словарь серверов из словаря старого формата ЖР для конкретной базы
        ports_main                                              =   {}                                                  # словарь главных портов из словаря старого формата ЖР для конкретной базы
        ports_add                                               =   {}                                                  # словарь дополнительных портов из словаря старого формата ЖР для конкретной базы
        tran_fix_list                                           =   {}                                                  # список событий, для который нужно менять тип транзакции на старом ЖР
        ext_main_id                                             =   {}                                                  # словарь ID разделителя основных данных
        ext_add_id                                              =   {}                                                  # словарь ID разделителя вспомогательных данных
        ext_area_main_ids                                       =   {}                                                  # словарь соответствий областей основных данных и указателей на них
        ext_area_add_ids                                        =   {}                                                  # словарь соответствий областей вспомогательных данных и указателей на них
# ======================================================================================================================
# ======= настройки программы ==========================================================================================
# ======= чтобы не было исключений, всё, внутри conf в строковом виде хранится. ПОМНИМ ОБ ЭТОМ =========================
# ======================================================================================================================
class conf:
    filename                                                    =   ""                                                  # имя файла конфигурации
    # ======= настройки специфики 1с ===================================================================================
    class c1:
        section_name                                            =   "1C settings"                                       # имя секции для файла конфигурации
        srvinfo                                                 =   ""                                                  # название говорит само за себя - имя каталога с информационными базами 1С
        cluster_file                                            =   "1CV8Clst.lst"                                      # имя файла кластера, предопределено
        cluster_file_o                                          =   "1CV8Clsto.lst"                                     # предпочтительно - его
        jr_dir                                                  =   "1Cv8Log"                                           # имя каталога журнала регистрации, предопределено
        jr_new_fname                                            =   "1Cv8.lgd"                                          # имя файла с новым ЖР в формате Sqlite3, предопределено
        jr_old_dict_fname                                       =   "1Cv8.lgf"                                          # имя файла словаря старого формата ЖР, предопределено

    # ======= настройки cherrypy =======================================================================================
    class http:
        section_name                                            =   "HTTP settings"                                     # имя секции для файла конфигурации
        listen_interface                                        =   os.getenv('HTTP_LISTEN_INTERFACE', '0.0.0.0')
        listen_port                                             =   os.getenv('HTTP_LISTEN_PORT', '8984')

    # ======= настройки ClickHouse =====================================================================================
    class clickhouse:
        section_name                                            =   "ClickHouse settings"                               # имя секции для файла конфигурации
        enabled                                                 =   os.getenv('CLICKHOUSE_ENABLED', 'False').lower() in ('true', '1', 't', 'y', 'yes')
        host                                                    =   os.getenv('CLICKHOUSE_HOST', 'localhost')
        port                                                    =   int(os.getenv('CLICKHOUSE_PORT', 9000))
        user                                                    =   os.getenv('CLICKHOUSE_USER', 'default')
        password                                                =   os.getenv('CLICKHOUSE_PASSWORD', '')
        database                                                =   os.getenv('CLICKHOUSE_DATABASE', 'zhr1c')

    # ======= настройки Redis ==========================================================================================
    class redis:
        section_name                                            =   "Redis settings"
        enabled                                                 =   os.getenv('REDIS_ENABLED', 'False').lower() in ('true', '1', 't', 'y', 'yes')
        server_path                                             =   ""                                                  # путь к redis-server (если нужно запускать)
        host                                                    =   os.getenv('REDIS_HOST', '127.0.0.1')
        port                                                    =   int(os.getenv('REDIS_PORT', 6379))
        db                                                      =   int(os.getenv('REDIS_DB', 0))
        dir                                                     =   ""                                                  # каталог для БД redis (для persistence)

    # ======= настройки solr ===========================================================================================
    class solr:
        section_name                                            =   "Solr settings"                                     # имя секции для файла конфигурации
        enabled                                                 =   os.getenv('SOLR_ENABLED', 'False').lower() in ('true', '1', 't', 'y', 'yes')
        mem_min                                                 =   os.getenv('SOLR_MEM_MIN', '2g')
        mem_max                                                 =   os.getenv('SOLR_MEM_MAX', '32g')
        dir                                                     =   os.getenv('SOLR_DIR', '')
        listen_interface                                        =   os.getenv('SOLR_LISTEN_INTERFACE', '127.0.0.1')
        listen_port                                             =   os.getenv('SOLR_LISTEN_PORT', '8983')
        solr_host                                               =   os.getenv('SOLR_HOST', '127.0.0.1')
        solr_port                                               =   os.getenv('SOLR_PORT', '8983')
        threads                                                 =   os.getenv('SOLR_THREADS', '12')
        java_home                                               =   os.getenv('SOLR_JAVA_HOME', '')
        wait_after_start                                        =   3                                                   # сколько сек подождать после старта
        ping                                                    =   "/admin/ping"                                       # указатель на страничку с пингом
        schema                                                  =   '<?xml version="1.0" encoding="UTF-8" ?>\r\n\r\n<schema name="journal2ct" version="1.0">\r\n\r\n  <field name="id"        type="pint"        indexed="true" stored="true"  multiValued="false"/>\r\n  <field name="pos"       type="plong"       indexed="true" stored="true"  multiValued="false" omitNorms="true"/>\r\n  <field name="len"       type="pint"        indexed="true" stored="true"  multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r1"        type="plong"       indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r1nmb"     type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r2"        type="string"      indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r3"        type="plong"       indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r3a"       type="plong"       indexed="true" stored="false" multiValued="false" omitNorms="true"/>  \r\n  <field name="r4"        type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r5"        type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r6"        type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r7"        type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r8"        type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r9"        type="string"      indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r10"       type="text_simple" indexed="true" stored="false" multiValued="false"/>\r\n  <field name="r11"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r12"       type="text_simple" indexed="true" stored="false" multiValued="false"/>\r\n  <field name="r13"       type="text_simple" indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r14"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r15"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r16"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r17"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r18"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n  <field name="r19"       type="pint"        indexed="true" stored="false" multiValued="false" omitNorms="true"/>\r\n\r\n\r\n<!--  <field name="text"      type="text_simple" indexed="true" stored="false" multiValued="true" />-->\r\n\r\n  <fieldType name="string"       class="solr.StrField"       docValues="false"	sortMissingLast="true"/>\r\n  <fieldType name="plong"        class="solr.LongPointField" docValues="false"/>\r\n  <fieldType name="pint"         class="solr.IntPointField"  docValues="false"/>\r\n  <fieldType name="puuid"        class="solr.UUIDField"      docValues="false"/>\r\n\r\n  <fieldType name="text_simple"  class="solr.TextField"      docValues="false" positionIncrementGap="0">\r\n    <analyzer>\r\n      <tokenizer class="solr.StandardTokenizerFactory"/>\r\n      <filter class="solr.LowerCaseFilterFactory"/>\r\n    </analyzer>\r\n  </fieldType>\r\n\r\n</schema>'  # файл schema для создания нового core\r\n
        config                                                  =   '<?xml version="1.0" encoding="UTF-8" ?>\r\n<config>\r\n  <luceneMatchVersion>8.0.0</luceneMatchVersion>\r\n\r\n  <!-- Load Data Import Handler and Apache Tika (extraction) libraries -->\r\n  <lib dir="${solr.install.dir:../../../..}/dist/" regex="solr-dataimporthandler-.*\\.jar"/>\r\n  <lib dir="${solr.install.dir:../../../..}/contrib/extraction/lib" regex=".*\\.jar"/>\r\n\r\n  <requestHandler name="/select" class="solr.SearchHandler">\r\n    <lst name="defaults">\r\n      <str name="echoParams">explicit</str>\r\n      <str name="df">text</str>\r\n    </lst>\r\n  </requestHandler>\r\n\r\n  <updateRequestProcessorChain name="dedupe">\r\n    <processor class="solr.LogUpdateProcessorFactory" />\r\n    <processor class="solr.RunUpdateProcessorFactory" />\r\n  </updateRequestProcessorChain>\r\n</config>\r\n' # файл конфигурации ядра solr для создания нового\r\n
        ##  эти записи ниже - отладочный. Они - с сохранением значений при парсинге. потом их закомментировать
        #schema                                                  =   '<?xml version="1.0" encoding="UTF-8" ?>\r\n\r\n<schema name="journal2ct" version="1.0">\r\n\r\n  <field name="id"        type="string"      indexed="true" stored="true"  multiValued="false"/>\r\n  <field name="pos"       type="plong"       indexed="true" stored="true"  multiValued="false" omitNorms="true"/>\r\n  <field name="len"       type="pint"        indexed="true" stored="true"  multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r1"        type="plong"       indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r1nmb"     type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r2"        type="string"      indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r3"        type="plong"       indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r3a"       type="plong"       indexed="true" stored="true" multiValued="false" omitNorms="true"/>  \r\n  <field name="r4"        type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r5"        type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r6"        type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r7"        type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r8"        type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r9"        type="string"      indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r10"       type="text_simple" indexed="true" stored="true" multiValued="false"/>\r\n  <field name="r11"       type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r12"       type="text_simple" indexed="true" stored="true" multiValued="false"/>\r\n  <field name="r13"       type="text_simple" indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r14"       type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n\r\n  <field name="r15"       type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r16"       type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n  <field name="r17"       type="pint"        indexed="true" stored="true" multiValued="false" omitNorms="true"/>\r\n\r\n\r\n<!--  <field name="text"      type="text_simple" indexed="true" stored="true" multiValued="true" />-->\r\n\r\n  <fieldType name="string"       class="solr.StrField"       docValues="false"	sortMissingLast="true"/>\r\n  <fieldType name="plong"        class="solr.LongPointField" docValues="false"/>\r\n  <fieldType name="pint"         class="solr.IntPointField"  docValues="false"/>\r\n  <fieldType name="puuid"        class="solr.UUIDField"      docValues="false"/>\r\n\r\n  <fieldType name="text_simple"  class="solr.TextField"      docValues="false" positionIncrementGap="0">\r\n    <analyzer>\r\n      <tokenizer class="solr.StandardTokenizerFactory"/>\r\n      <filter class="solr.LowerCaseFilterFactory"/>\r\n    </analyzer>\r\n  </fieldType>\r\n\r\n</schema>'  # файл schema для создания нового core\r\n
        #config                                                  =   '<?xml version="1.0" encoding="UTF-8" ?>\r\n<config>\r\n  <luceneMatchVersion>7.2.1</luceneMatchVersion>\r\n\r\n  <!-- Load Data Import Handler and Apache Tika (extraction) libraries -->\r\n  <lib dir="${solr.install.dir:../../../..}/dist/" regex="solr-dataimporthandler-.*\\.jar"/>\r\n  <lib dir="${solr.install.dir:../../../..}/contrib/extraction/lib" regex=".*\\.jar"/>\r\n\r\n  <requestHandler name="/select" class="solr.SearchHandler">\r\n    <lst name="defaults">\r\n      <str name="echoParams">explicit</str>\r\n      <str name="df">text</str>\r\n    </lst>\r\n  </requestHandler>\r\n\r\n  <updateRequestProcessorChain name="dedupe">\r\n    <processor class="solr.LogUpdateProcessorFactory" />\r\n    <processor class="solr.RunUpdateProcessorFactory" />\r\n  </updateRequestProcessorChain>\r\n</config>\r\n' # файл конфигурации ядра solr для создания нового\r\n
# ======================================================================================================================
# всё, касающееся потоков парсинга
# ======================================================================================================================
class parser:
    section_name                                                =   "Parser settings"                                   # имя секции для файла конфигурации
    threads                                                     =   os.getenv('PARSER_THREADS', '')
    maxrecsize                                                  =   512                                                 # сколько записей отправляем в ClickHouse
    ibases                                                      =   []                                                  # полный каталог др базы, имя базы, формат жр базы
    state_file                                                  =   ""                                                  # файл с информацией об статусе обработки отдельных файлов
    state_file_lock                                             =   False                                               # однопоточная запись или чтение в файл статусов
    solr_id_file                                                =   ""                                                  # файл-итератор имён файлов для хранения ссылки только в SOLR
    solr_id_file_lock                                           =   False                                               # однопоточная запись или чтение в файл-итератор
    blocksize                                                   =   16384                                               # размер блока для чтения из файла
    bytes_2_commit                                              =   200000                                              # по сколько байт коммитить в solr
    maxblocksize                                                =   8388608                                             # больше такого размера блоки не читать - 8МБ
    lgd_parse_records_limit                                     =   50000                                               # величина обрабатываемых записей за 1 проход
    lgd_select_last_id                                          =   ''' select rowID from EventLog 
                                                                        order by rowID desc limit 1 '''                 # выбор ID последней записи LGD
    lgd_select_first_id                                         =   ''' select rowID from EventLog 
                                                                        order by rowID asc limit 1 '''                  # выбор ID первой записи. У обрезанных ЖР она будет >1
# ======================================================================================================================
# всё, касающееся отладки
# ======================================================================================================================
class debug:
    on                                                          =   os.getenv('DEBUG_ENABLED', 'True').lower() in ('true', '1', 't', 'y', 'yes')
    on_parser                                                   =   os.getenv('DEBUG_PARSER', 'False').lower() in ('true', '1', 't', 'y', 'yes')
    filehandle                                                  =   None                                                # указатель на файл лога отладки
    filename                                                    =   ""                                                  # имя файла лога для отладки
    dir                                                         =   ""
# ======================================================================================================================
# здесь описаны все используемые регулярки
# ======================================================================================================================
class rexp:
    service_is_1c                                               =   re.compile(r'\\ragent.*\-d' , flags=re.IGNORECASE)  # имя службы 1с
    daemon_1c                                                   =   re.compile(r'srv1cv8.*'     , flags=re.IGNORECASE)  # имя службы 1с
    enviroments                                                 =   re.compile(r'(\w+)=(".*?"|\'.*?\'|\S*)')            # получение переменных окружения
    service_1c_workdir                                          =   re.compile(r'\-d\s*\$*[\"\{](.+?)[\"\}]')           # получение рабочего каталога из пути к службе 1с
    any_filename                                                =   re.compile(r'[^\\/]*?$')                            # любое имя файла - последние символы после \ или /
    any_file_ext                                                =   re.compile(r'[^\.]*?$')                             # любое расширение файла - последние символы после точки
    uuid_start                                                  =   re.compile(r'^[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}')# UUID c самого начала строки!
    is_1c_cluster                                               =   re.compile(r'reg_\d+',flags=re.IGNORECASE)          # проверка имени каталога на шаблон кластера 1с
    clst_1c_base_rec                                            =   re.compile(r'\{([а-яА-ЯёЁйЙ\(\)\s\w\-]+),"(.*?)",".*?",".*?",".*?",".*?",".*?",".*?",".*?Srvr=',flags=re.IGNORECASE)# шаблон для получения идентификатора базы из файла 1CV8Clst.lst #2019.01.28 https://github.com/WonderMr/Journal2Ct/issues/42
    is_lgP_file_re                                              =   re.compile(r'\.lgp$')
    is_lgD_file_re                                              =   re.compile(r'\.lgd$')
    bad_chunk_pos                                               =   re.compile(r'position\s(\d+)')                      # смещение плохого чанка при побайтовом чтении
    del_quotes                                                  =   re.compile(r'^"|"$')                                # для удаления кавычек в начале и конце строки
    find_1c_link                                                =   re.compile(r'([\w\d]+\:[\w\d]+)')                   # ссылка для внутренних ссылок 1С
    # универсальная регулярка записи ЖР c отбором для выбора
    sel_re                                                      =   r'\,*\r*\n*\{(\d{14}),(\w),\r*\n\{([0-9a-f]+),([0-9a-f]+)\},(\d+),(\d+),(\d+),(\d+),(\d+),(\w),"([^ꡏ]*?)(?=",\d+,\r*\n)",(\d+),\r*\n\{([^ꡏ]*?)(?=\},")\},"([^ꡏ]*?)(?=",\d+)",(\d+),(\d+),(\d+),(\d+),\d+[,\d+]*,\r*\n\{((\d+)|\d+,(\d+),(\d+),(\d+),(\d+))\}\r*\n\},*\r*\n*' #case 2020.05.21
    sel_re_ext_nmb                                              =   22                                                  # если есть дополнительные области, то length(sel_re)>sel_re_ext #case 2020.05.21
    my_sel_re                                                   =   re.compile(sel_re);
    # а это старая, без выбора
    #my_re                                                       =   re.compile(r'\,*\r*\n*\{\d{14},\w,\r*\n\{[0-9a-f]+,[0-9a-f]+\},\d+,\d+,\d+,\d+,\d+,\w,"[А-ЯA-Zа-яa-z\Ё\ё\d\n\r\s\.\,\:\;\(\)\{\}\<\>\[\]\«\»\=\/\~\'\"\_\\\#\!\&\%\$\@\#\^\*\+\-\?\№\¶]*?(?=",\d+,\r*\n)",\d+,\r*\n\{[А-ЯA-Zа-яa-z\Ё\ё\d\n\r\s\.\,\:\;\(\)\{\}\<\>\[\]\«\»\=\/\~\'\"\_\\\#\!\&\%\$\@\#\^\*\+\-\?\№\¶]*?(?=\},")\},"[А-ЯA-Zа-яa-z\Ё\ё\d\n\r\s\.\,\:\;\(\)\{\}\<\>\[\]\«\»\=\/\~\'\"\_\\\#\!\&\%\$\@\#\^\*\+\-\?\№\¶]*?(?=",\d+)",\d+,\d+,\d+,\d+,\d+[,\d+]*,\r*\n\{[\d,*]+\}\r*\n\},*\r*\n*');
    # универсальная регулярка записи ЖР с отбором полей для парсинга
    my_parse_re                                                 =   re.compile("("+sel_re+")");
    # отбор данных их словарей файловых ЖР ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    class dict:
        users_re                                                =   re.compile(r'\{1,([\w\d]{8}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{12}),"(.*?)",(\d+)}')# выбор всех пользователей из словаря старого формата ЖР
        computers_re                                            =   re.compile(r'\{2,"(.*?)",(\d+)}')                   # выбор всех рабочих станций из словаря старого формата ЖР
        applications_re                                         =   re.compile(r'\{3,"(.*?)",(\d+)}')                   # выбор всех приложений из словаря старого формата ЖР
        actions_re                                              =   re.compile(r'\{4,"(.*?)",(\d+)}')                   # выбор всех непредопределённых событий из словаря старого формата ЖР
        metadata_re                                             =   re.compile(r'\{5,([\w\d]{8}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{12}),"(.*?)",(\d+)}')# выбор всех метаданных из словаря старого формата ЖР
        servers_re                                              =   re.compile(r'\{6,"(.*?)",(\d+)}')                   # выбор всех серверов из словаря старого формата ЖР
        ports_main_re                                           =   re.compile(r'\{7,(\d+),(\d+)}')                     # выбор всех главных портов из словаря старого формата ЖР
        ports_add_re                                            =   re.compile(r'\{8,(\d+),(\d+)}')                     # выбор всех дополнительных портов из словаря старого формата ЖР
        ext_id                                                  =   re.compile(r'\{9,([\w\d]{8}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{12}),"(.*)",(\d+)}') # выбор ID для обозначения области данных
        #ext_add_id                                              =   re.compile(r'^\{9,([\w\d]{8}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{4}\-[\w\d]{12}),"(ОбластьДанныхВспомогательныеДанные|РћР±Р»Р°СЃС‚СЊР”Р°РЅРЅС‹С…Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹РµР”Р°РЅРЅС‹Рµ)",(\d+)}') # выбор ID для обозначения ОбластьДанныхВспомогательныеДанные
        ext_area_id                                             =   re.compile(r'{"N",(\d+)},(\d+),(\d+)}')             # собственно, это и есть сслыка на область данных, а так же обозначение, основная оно или вспомогательная, ;$1 = номер области, $2 - признак основные или вспомогательные, $3 - закондированый идентификатор
    # разбор данных запроса от обработки ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    class q:
        ref_re                                                  =   re.compile(r'ref=(.+?)(?=&)')                       # имя информационной базы
        date_start                                              =   re.compile(r'ДатаНачала=(.+)')                      # r1 начало периода отбора
        date_end                                                =   re.compile(r'ДатаОкончания=(.+)')                   # r1 конец периода отбора
        trans_status_re                                         =   re.compile(r'СтатусТранзакции=(.+)')                # r2 отбор по статусу транзации
        user_re                                                 =   re.compile(r'Пользователь=(.+)')                    # r4 имя пользователя информационной базы
        computer_re                                             =   re.compile(r'Компьютер=(.+)')                       # r5 имя компьютера пользователя информационной базы
        application_re                                          =   re.compile(r'ИмяПриложения=(.+)')                   # r6 имя приложения пользователя информационной базы
        connections_re                                          =   re.compile(r'Соединение=(.+)')                      # r7
        action_re                                               =   re.compile(r'Событие=(.+)')                         # r8 имя отбираемого события
        level_re                                                =   re.compile(r'Уровень=(.+)')                         # r9 уровень отбора - может принимать значения Информация,Ошибка,Предупреждение,Примечание
        comments_re                                             =   re.compile(r'Комментарий="(.+?)(?=")')              # r10 отбор по комментарию
        metadata_re                                             =   re.compile(r'Метаданные=(.+)')                      # r11 метаданные отбираемого события
        data_re                                                 =   re.compile(r'^Данные=(.+)$')                        # r12 данные отбираемого события
        data_presentation_re                                    =   re.compile(r'ПредставлениеДанных="(.+)(?=")')       # r13 отбор по представлению данных
        server_re                                               =   re.compile(r'РабочийСервер=(.+)')                   # r14 имя сервера из запроса отбора событий
        port_main_re                                            =   re.compile(r'ОсновнойIPПорт=(.+)')                  # r15 основной порт из отбора событий
        port_add_re                                             =   re.compile(r'ВспомогательныйIPПорт=(.+)')           # r16 дополнительный порт порт из отбора событий
        seans_re                                                =   re.compile(r'Сеанс=(.+)')                           # r17 ID сеанса, передаётся без словаря
        ext_main                                                =   re.compile(r'РазделениеОсновныеДанные=(.+)')        # r18(21) разделение данных основные данные #case 2020.05.21
        ext_add                                                 =   re.compile(r'РазделениеВспомогательныеДанные=(.+)') # r19(22) разделение данных основные данные #case 2020.05.21
        amount_re                                               =   re.compile(r'КоличествоСобытий=(.+)')               # количество событий из отбора. число
# ======================================================================================================================
# все потоки хранятся в этих переменных
# ======================================================================================================================
class threads:
    solr                                                        =   None                                                # в этом потоке запускается Solr
    cherry                                                      =   None                                                # вишенка живёт в этом потоке
    parser                                                      =   None                                                # поток для парсера старого формата ЖР
    parser_new                                                  =   None                                                # поток для парсера нового формата ЖР
    config_updater                                              =   None                                                # поток для обновления списка баз
    warming_cache                                               =   None                                                # поток для прогревания кэша
    parser2                                                     =   None                                                # поток для парсера старого формата ЖР
    parser_new2                                                 =   None                                                # поток для парсера нового формата ЖР
    redis                                                       =   None                                                # поток управления процессом Redis
    sender                                                      =   None                                                # поток отправки данных из очереди
# ======================================================================================================================
# все ожидания опеределены здесь
# ======================================================================================================================
class waits:
    parser_sleep_on_update_filelist                             =   30                                                  # пауза между обновлениями списка файлов
    warming_cache_wait                                          =   300                                                 # интервал между програваниями кэша
    sleep_on_conf_detection                                     =   15                                                  # добавление или удаление баз будет происходить в этом интервале
    read_state_exception                                        =   1                                                   # пауза на ошибке при чтении или записи в файл состояния
    in_cycle_we_trust                                           =   0.01
    solr_on_bad_send_to                                         =   0.1
    solr_wait_start                                             =   5
    solr_cycles                                                 =   10                                                  # сколько раз пробуем отправить запрос к Solr

# ======================================================================================================================
# класс с именами для полей
# ======================================================================================================================
class nms:
    class ib:
        name                                                    =   "ibase_name"                                        # имя раздела базы в файле конфигурации, предопределено
        jr_dir                                                  =   "ibase_jr_dir"                                      # имя раздела пути к каталогу ЖР в файле конфигурации, предопределено
        jr_format                                               =   "ibase_jr_format"                                   # имя раздела формата ЖР в файле конфигурации, предопределено
        jr_format_new                                           =   "lgd"                                               # расширение файла нового формата ЖР, предопределено
        jr_format_old                                           =   "lgf"                                               # расширение файла старого формата ЖР, предопределено
        total_size                                              =   "total_size"                                        # сколько всего занимает ЖР базы, в байтах или количестве записей
        parsed_size                                             =   "parsed_size"                                       # размер распарсенных данных, в байтах или количестве записей
# ======================================================================================================================
# класс кэшей
# ======================================================================================================================
class cache:
    filesizes                                                   =   []                                                  # кэш размеров файлов для прохода по списку при  чтении
    file_ids                                                    =   []                                                  # кэш id-файлов для прохода по списку при  чтении
# ======================================================================================================================
# всё, касающееся отправки уведомлений
# ======================================================================================================================
class notify:
    filehandle                                                  =   None                                                # указатель на файл лога
    filename                                                    =   ""                                                  # имя файла лога для
    select_user_re                                              =   re.compile(r',"(.*)?"')                             # выбор имени пользователя из события логина
    failed_logons                                               =   {}                                                  # список айдишников для _$Session$_.AuthenticationError по базам
