# -*- coding: utf-8 -*-
import  os
##### limitation start
#import  platform
#import  socket
##### limitation end
# ======================================================================================================================
from    src.tools           import  tools                   as  t
from    src                 import  globals                 as  g
# ======================================================================================================================
# 2018.07.14 В этом классе описаны специфичные для 1С типы словарей
# ======================================================================================================================
class dictionary():
    # ------------------------------------------------------------------------------------------------------------------
    actions                                                 =   {}                                                      # события ЖР
    actions['_$Access$_.Access']                            =   'Доступ. Доступ'
    actions['_$Access$_.AccessDenied']                      =   'Доступ. Отказ в доступе'
    actions['_$Data$_.Delete']                              =   'Данные. Удаление'
    actions['_$Data$_.DeletePredefinedData']                =   'Данные. Удаление предопределенных данных'
    actions['_$Data$_.DeleteVersions']                      =   'Данные. Удаление версий'
    actions['_$Data$_.New']                                 =   'Данные. Добавление'
    actions['_$Data$_.NewPredefinedData']                   =   'Данные. Добавление предопределенных данных'
    actions['_$Data$_.NewVersion']                          =   'Данные. Добавление версии'
    actions['_$Data$_.Post']                                =   'Данные. Проведение'
    actions['_$Data$_.PredefinedDataInitialization']        =   'Данные. Инициализация предопределенных данных'
    actions[
        '_$Data$_.PredefinedDataInitializationDataNotFound']=   'Данные. Инициализация предопределенных данных. Данные не найдены'
    actions['_$Data$_.SetPredefinedDataInitialization']     =   'Данные. Установка инициализации предопределенных данных'
    actions['_$Data$_.SetStandardODataInterfaceContent']    =   'Данные. Изменение состава стандартного интерфейса OData'
    actions['_$Data$_.TotalsMaxPeriodUpdate']               =   'Данные. Изменение максимального периода рассчитанных итогов'
    actions['_$Data$_.TotalsMinPeriodUpdate']               =   'Данные. Изменение минимального периода рассчитанных итогов'
    actions['_$Data$_.Unpost']                              =   'Данные. Отмена проведения'
    actions['_$Data$_.Update']                              =   'Данные. Изменение'
    actions['_$Data$_.UpdatePredefinedData']                =   'Данные. Изменение предопределенных данных'
    actions['_$Data$_.VersionCommentUpdate']                =   'Данные. Изменение комментария версии'
    actions['_$InfoBase$_.ConfigExtensionUpdate']           =   'Информационная база. Изменение расширения конфигурации'
    actions['_$InfoBase$_.ConfigUpdate']                    =   'Информационная база. Изменение конфигурации'
    actions['_$InfoBase$_.DBConfigBackgroundUpdateCancel']  =   'Информационная база. Отмена фонового обновления'
    actions['_$InfoBase$_.DBConfigBackgroundUpdateFinish']  =   'Информационная база. Завершение фонового обновления'
    actions['_$InfoBase$_.DBConfigBackgroundUpdateResume']  =   'Информационная база. Продолжение (после приостановки) процесса фонового обновления'
    actions['_$InfoBase$_.DBConfigBackgroundUpdateStart']   =   'Информационная база. Запуск фонового обновления'
    actions['_$InfoBase$_.DBConfigBackgroundUpdateSuspend'] =   'Информационная база. Приостановка (пауза) процесса фонового обновления'
    actions['_$InfoBase$_.DBConfigExtensionUpdate']         =   'Информационная база. Изменение расширения конфигурации базы данных'
    actions['_$InfoBase$_.DBConfigExtensionUpdateError']    =   'Информационная база. Ошибка изменения расширения конфигурации базы данных'
    actions['_$InfoBase$_.DBConfigUpdate']                  =   'Информационная база. Изменение конфигурации базы данных'
    actions['_$InfoBase$_.DBConfigUpdateError']             =   'Информационная база. Ошибка изменения конфигурации базы данных'
    actions['_$InfoBase$_.DBConfigUpdateStart']             =   'Информационная база. Запуск обновления конфигурации базы данных'
    actions['_$InfoBase$_.DumpFinish']                      =   'Информационная база. Окончание выгрузки в файл'
    actions['_$InfoBase$_.DumpStart']                       =   'Информационная база. Начало выгрузки в файл'
    actions['_$InfoBase$_.EraseData']                       =   'Информационная база. Удаление данных информационной баз'
    actions['_$InfoBase$_.EventLogSettingsUpdate']          =   'Информационная база. Изменение параметров журнала регистрации'
    actions['_$InfoBase$_.InfoBaseAdmParamsUpdate']         =   'Информационная база. Изменение параметров информационной базы'
    actions['_$InfoBase$_.MasterNodeUpdate']                =   'Информационная база. Изменение главного узла'
    actions['_$InfoBase$_.PredefinedDataUpdate']            =   'Информационная база. Обновление предопределенных данных'
    actions['_$InfoBase$_.RegionalSettingsUpdate']          =   'Информационная база. Изменение региональных установок'
    actions['_$InfoBase$_.RestoreStart']                    =   'Информационная база. Начало загрузки из файла'
    actions['_$InfoBase$_.RestoreFinish']                   =   'Информационная база. Окончание загрузки из файла'
    actions['_$InfoBase$_.SetPredefinedDataUpdate']         =   'Информационная база. Установить обновление предопределенных данных'
    actions['_$InfoBase$_.TARImportant']                    =   'Тестирование и исправление. Ошибка'
    actions['_$InfoBase$_.TARInfo']                         =   'Тестирование и исправление. Сообщение'
    actions['_$InfoBase$_.TARMess']                         =   'Тестирование и исправление. Предупреждение'
    actions['_$Job$_.Cancel']                               =   'Фоновое задание. Отмена'
    actions['_$Job$_.Fail']                                 =   'Фоновое задание. Ошибка выполнения'
    actions['_$Job$_.Start']                                =   'Фоновое задание. Запуск'
    actions['_$Job$_.Succeed']                              =   'Фоновое задание. Успешное завершение'
    actions['_$Job$_.Terminate']                            =   'Фоновое задание. Принудительное завершение'
    actions['_$OpenIDProvider$_.NegativeAssertion']         =   'Провайдер OpenID. Отклонено'
    actions['_$OpenIDProvider$_.PositiveAssertion']         =   'Провайдер OpenID. Подтверждено'
    actions['_$PerformError$_']                             =   'Ошибка выполнения'
    actions['_$Session$_.Authentication']                   =   'Сеанс. Аутентификация'
    actions['_$Session$_.AuthenticationError']              =   'Сеанс. Ошибка аутентификации'
    actions['_$Session$_.ConfigExtensionApplyError']        =   'Сеанс. Ошибка применения расширения конфигурации'
    actions['_$Session$_.Finish']                           =   'Сеанс. Завершение'
    actions['_$Session$_.Start']                            =   'Сеанс. Начало'
    actions['_$Transaction$_.Begin']                        =   'Транзакция. Начало'
    actions['_$Transaction$_.Commit']                       =   'Транзакция. Фиксация'
    actions['_$Transaction$_.Rollback']                     =   'Транзакция. Отмена'
    actions['_$User$_.Delete']                              =   'Пользователи. Удаление'
    actions['_$User$_.New']                                 =   'Пользователи. Добавление'
    actions['_$User$_.NewError']                            =   'Пользователи. Ошибка добавления'
    actions['_$User$_.Update']                              =   'Пользователи. Изменение'
    actions['_$User$_.UpdateError']                         =   'Пользователи. Ошибка изменения'
    # есть ещё такое, но пока не встретил его "Пользователи.Ошибка обновления даты последней активности"
    # ------------------------------------------------------------------------------------------------------------------
    clients                                                 =   {}                                                      # типы клиентов по внутреннему наименованию
    clients['BackgroundJob']                                =   'Фоновое задание'
    clients['1CV8']                                         =   'Толстый клиент'
    clients['1CV8C']                                        =   'Тонкий клиент'
    clients['Designer']                                     =   'Конфигуратор'
    clients['WebClient']                                    =   'Веб-Клиент'
    clients['COMConnection']                                =   'COM-соединение'
    clients['WSConnection']                                 =   'сессия Web-сервиса'
    clients['SystemBackgroundJob']                          =   'Системное фоновое задание'
    clients['SrvrConsole']                                  =   'Консоль кластера'
    clients['COMConsole']                                   =   'COM-администратор'
    clients['JobScheduler']                                 =   'Планировщик заданий'
    clients['Debugger']                                     =   'Отладчик'
    clients['RAS']                                          =   'Сервер администрирования'
    clients['HTTPServiceConnection']                        =   'Cоединение c HTTP-сервисом'
    clients['ODataConnection']                              =   'Соединение с автоматическим REST API'
    # ------------------------------------------------------------------------------------------------------------------
    severity                                                =   {}
    severity['0']                                           =   'N'                                                     # в старом N, в новом - 0 - Примечание - Note
    severity['1']                                           =   'I'                                                     # в старом I, в новом - 1 - Информация
    severity['2']                                           =   'W'                                                     # в старом W, в новом - 2 - Предупреждение - Warning
    severity['3']                                           =   'E'                                                     # в старом E, в новом - 3 - Ошибка - Error
    # ------------------------------------------------------------------------------------------------------------------
    trans_state                                             =   {}
    trans_state['0']                                        =   'R'                                                     #
    trans_state['1']                                        =   'U'                                                     #
    trans_state['2']                                        =   'C'                                                     #
    trans_state['3']                                        =   'N'                                                     #
    # ------------------------------------------------------------------------------------------------------------------
    # 2018.07.14 Функция чтения содержимого словаря старого формата ЖР в глобальную переменную, соответствующую базе
    # при повторном вызове вернётся, если словарь не изменился. Если изменился - перечитает
    # ------------------------------------------------------------------------------------------------------------------
    def read_ib_dictionary(rib_name):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # сначала проверю наличие базы в глобальном конфиге
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # t.debug_print("start read dictionary")
        try:
            ib_dict_file                                        =   ""
            for element in g.parser.ibases:
                if element[g.nms.ib.name].upper()               ==  rib_name.upper():                                   # сравниванием в верхнем регистре
                    ib_dict_file                                =   element[g.nms.ib.jr_dir]+\
                                                                    (
                                                                        "/1Cv8.lgf" \
                                                                        if element[g.nms.ib.jr_format] == 'lgf'
                                                                        else "/1Cv8.lgd"
                                                                    )
            if(not os.path.exists(ib_dict_file)):
                t.debug_print(f"════════════════════════════════════════════════════════════════")
                t.debug_print(f"✗ ОШИБКА: Словарь журнала регистрации не найден!")
                t.debug_print(f"  База: {rib_name}")
                t.debug_print(f"  Ожидаемый путь: {ib_dict_file}")
                t.debug_print(f"════════════════════════════════════════════════════════════════")
                t.debug_print(f"Возможные причины:")
                t.debug_print(f"  1. Неверно указан путь IBASE_0_JR в файле .env")
                t.debug_print(f"  2. База данных 1С не существует по указанному пути")
                t.debug_print(f"  3. Журнал регистрации отключен в базе 1С")
                t.debug_print(f"════════════════════════════════════════════════════════════════")
                t.debug_print(f"Как исправить:")
                t.debug_print(f"  1. Найдите каталог журнала вашей базы 1С:")
                t.debug_print(f"     find /home/usr1cv8/.1cv8 -name '1Cv8Log' -type d")
                t.debug_print(f"  2. Укажите найденный путь в .env:")
                t.debug_print(f"     IBASE_0_JR=/правильный/путь/к/1Cv8Log")
                t.debug_print(f"  3. Перезапустите приложение")
                t.debug_print(f"════════════════════════════════════════════════════════════════")
                t.graceful_shutdown(3)
                return
            if g.rexp.is_lgD_file_re.findall(ib_dict_file):
                dictionary.read_new_ib_dictionary(rib_name, ib_dict_file)
            else:
                dictionary.read_old_ib_dictionary(rib_name, ib_dict_file)
        except Exception as e:
            t.debug_print(f"read_ib_dictionary exception = {str(e)}", 'dictionary')
        # t.debug_print("end read dictionary")
    # ------------------------------------------------------------------------------------------------------------------
    # чтение словаря нового формата ЖР
    # ------------------------------------------------------------------------------------------------------------------
    def read_new_ib_dictionary(rib_name, rib_file_name):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        _dicts                                              =   g.execution.c1_dicts                                    # чуть подсокращу это длинное имя
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив пользователей
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_users                                           =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from UserCodes'
                                                                ):
            rib_users[str(rec[0])]                          =   {
                                                                'uuid'  :   rec[2],
                                                                'name'  :   rec[1]
                                                                }
        _dicts.users[rib_name]                              =   rib_users
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив рабочих станций
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_computers                                       =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from ComputerCodes'
                                                                ):
            rib_computers[str(rec[0])]                      =   g.rexp.del_quotes.sub('',rec[1])                        # и кавычки надо убрать
        _dicts.computers[rib_name]                          =   rib_computers
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив приложений
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_applications                                    =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from AppCodes'
                                                                ):
            rib_applications[str(rec[0])]                   =   g.rexp.del_quotes.sub('',rec[1])                        # и кавычки надо убрать
        _dicts.applications[rib_name]                       =   rib_applications
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив действий
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_actions                                         =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from EventCodes'
                                                                ):
            rib_actions[str(rec[0])]                        =   g.rexp.del_quotes.sub('',rec[1])                        # и кавычки надо убрать
        _dicts.actions[rib_name]                            =   rib_actions
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив метаданных
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_metadatas                                       =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from MetadataCodes'
                                                                ):
            rib_metadatas[str(rec[0])]                      =   {
                                                                'uuid'  :   rec[2],
                                                                'name'  :   rec[1]
                                                                }
        _dicts.metadata[rib_name]                           =   rib_metadatas
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив серверов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_servers                                         =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from WorkServerCodes'
                                                                ):
            rib_servers[str(rec[0])]                        =   g.rexp.del_quotes.sub('',rec[1])                        # и кавычки надо убрать
        _dicts.servers[rib_name]                            =   rib_servers
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив главных портов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_ports_main                                      =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from PrimaryPortCodes'
                                                                ):
            rib_ports_main[str(rec[0])]                     =   rec[1]
        _dicts.ports_main[rib_name]                         =   rib_ports_main
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив дополнительных портов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_ports_add                                       =   {}
        for rec                                             in  t.sqlite3_exec(
                                                                    rib_file_name,
                                                                    'select * from SecondaryPortCodes'
                                                                ):
            rib_ports_add[str(rec[0])]                      =   rec[1]
        _dicts.ports_add[rib_name]                          =   rib_ports_add
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # это костыль для разделения данных для нового формата, там он не включен
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            rib_ext_main_id                                     =   0
            rib_ext_add_id                                      =   0
            _dicts.ext_main_id[rib_name]                        =   rib_ext_main_id
            _dicts.ext_add_id[rib_name]                         =   rib_ext_add_id
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            rib_areas_main_ids                                  =   {}                                                  # список областей основных данных
            rib_areas_ext_ids                                   =   {}                                                  # список областей вспомогательных данных
            _dicts.ext_area_main_ids[rib_name]                  =   rib_areas_main_ids
            _dicts.ext_area_add_ids[rib_name]                   =   rib_areas_ext_ids
        except Exception as e:
            t.debug_print("bad data: "+str(e),"dictionary")
    # ------------------------------------------------------------------------------------------------------------------
    # 2018.07.14 Функция чтения содержимого словаря старого формата ЖР в глобальную переменную, соответствующую базе
    # при повторном вызове вернётся, если словарь не изменился. Если изменился - перечитает
    # ------------------------------------------------------------------------------------------------------------------
    def read_old_ib_dictionary(rib_name, rib_file_name):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # проверяем, не изменился ли размер словаря
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ib_dict_size                                        =   os.path.getsize(rib_file_name)
        _dicts                                              =   g.execution.c1_dicts                                    # чуть подсокращу это длинное имя
        if _dicts.dict_actual_filesizes.get(rib_name):                                                                  # если он уже есть
            if _dicts.dict_actual_filesizes[rib_name]       ==  ib_dict_size:                                           # размер файла не изменился
                return                                                                                                  # перечитывать словарь не нужно
        # читаем и разбираем файл
        rib_content                                         =   t.readfile(rib_file_name)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив пользователей
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_users                                           =   {}
        for rib_user in g.rexp.dict.users_re.findall(rib_content):
            rib_users[rib_user[2]]                          =   {
                                                                'uuid'  :   rib_user[0],
                                                                'name'  :   rib_user[1]
                                                                }
        _dicts.users[rib_name]                              =   rib_users
        # в конце устанавливаю размер прочитанного файла
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив рабочих станций
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_computers                                       =   {}
        for rib_computer in g.rexp.dict.computers_re.findall(rib_content):
            rib_computers[rib_computer[1]]                  =   rib_computer[0]
        _dicts.computers[rib_name]                          =   rib_computers
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив приложений
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_applications                                    =   {}
        for rib_application in g.rexp.dict.applications_re.findall(rib_content):
            rib_applications[rib_application[1]]            =   rib_application[0]
        _dicts.applications[rib_name]                       =   rib_applications
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив действий
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_actions                                         =   {}
        fix_act_tran_arr                                    =   []                                                      # локальный массив для исправления типов транзакций
        for rib_action in g.rexp.dict.actions_re.findall(rib_content):
            rib_actions[rib_action[1]]                      =   rib_action[0]
            if rib_action[0].find("_$Transaction$_.")       >   -1:                                                     # если это транзакция
                fix_act_tran_arr.append(rib_action[1])                                                                  # то нужно добавить в список корректировки символа
        _dicts.actions[rib_name]                            =   rib_actions
        _dicts.tran_fix_list[rib_name]                      =   fix_act_tran_arr
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив метаданных
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_metadatas                                       =   {}
        for rib_metadata in g.rexp.dict.metadata_re.findall(rib_content):
            rib_metadatas[rib_metadata[2]]                  =   {
                                                                'uuid'  :   rib_metadata[0],
                                                                'name'  :   rib_metadata[1]
                                                                }
        _dicts.metadata[rib_name]                           =   rib_metadatas
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив серверов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_servers                                         =   {}
        for rib_server in g.rexp.dict.servers_re.findall(rib_content):
            rib_servers[rib_server[1]]                      =   rib_server[0]
        _dicts.servers[rib_name]                            =   rib_servers
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив главных портов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_ports_main                                      =   {}
        for rib_port_main in g.rexp.dict.ports_main_re.findall(rib_content):
            rib_ports_main[rib_port_main[1]]                =   rib_port_main[0]
        _dicts.ports_main[rib_name]                         =   rib_ports_main
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # заполняю массив дополнительных портов
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        rib_ports_add                                       =   {}
        for rib_port_add in g.rexp.dict.ports_add_re.findall(rib_content):
            rib_ports_add[rib_port_add[1]]                  =   rib_port_add[0]
        _dicts.ports_add[rib_name]                          =   rib_ports_add
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # 2020.05.22 Обработка основных и вспомогательных данных
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            rib_ext_main_id                                     =   0
            rib_ext_add_id                                      =   0
            for rib_ext_id in g.rexp.dict.ext_id.findall(rib_content):                                                      # получаю ID областей основных данных
                if rib_ext_id[1]                                ==  "ОбластьДанныхОсновныеДанные":
                    rib_ext_main_id                             =   rib_ext_id[2]
                if rib_ext_id[1]                                ==  "ОбластьДанныхВспомогательныеДанные":
                    rib_ext_add_id                              =   rib_ext_id[2]
            _dicts.ext_main_id[rib_name]                        =   rib_ext_main_id
            _dicts.ext_add_id[rib_name]                         =   rib_ext_add_id
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            rib_areas_main_ids                                  =   {}                                                  # список областей основных данных
            rib_areas_ext_ids                                   =   {}                                                  # список областей вспомогательных данных
            for rib_area in g.rexp.dict.ext_area_id.findall(rib_content):
                if rib_area[1]                                  ==  _dicts.ext_main_id[rib_name]:                       #
                    rib_areas_main_ids[rib_area[2]]             =   rib_area[0]                                         # rib_area[2] - id в формате ЖР, rib_area[0] - номер области
                if rib_area[1]                                  ==  _dicts.ext_add_id[rib_name]:
                    rib_areas_ext_ids[rib_area[2]]              =   rib_area[0]
            _dicts.ext_area_main_ids[rib_name]                  =   rib_areas_main_ids
            _dicts.ext_area_add_ids[rib_name]                   =   rib_areas_ext_ids
        except Exception as e:
            t.debug_print("bad data: "+str(e),"dictionary")
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # устанавливаю актуальный размер файла словаря
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        _dicts.dict_actual_filesizes[rib_name]              =   ib_dict_size                                            #
    # ------------------------------------------------------------------------------------------------------------------
    # 2018.07.17 выбираем значение нужного элемента из простого массива
    # ------------------------------------------------------------------------------------------------------------------
    def get_simple_descr(gsr_arr,gsr_id):
        ret                                                 =   ""
        for each                                            in  gsr_arr:
            if each                                         ==  gsr_id:
                ret                                         =   gsr_arr[each]
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # 2018.07.17 выбираем id нужного элемента из простого массива
    # ------------------------------------------------------------------------------------------------------------------
    def get_simple_id(gsr_arr,gsr_descr):
        ret                                                 =   ""
        for each                                            in  gsr_arr:
            if gsr_arr[each]                                ==  gsr_descr:
                ret                                         =   each
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # 2018.07.17 выбираем значение сложного элемента массива
    # ------------------------------------------------------------------------------------------------------------------
    def get_complex_rec(gsr_arr,gsr_id):
        ret                                                 =   {}                                                      # ничего не нашёл, возвращаю пустые значения
        ret['uuid']                                         =   ""
        ret['name']                                         =   ""
        for each                                            in  gsr_arr:
            if each                                         ==  gsr_id:
                ret                                         =   gsr_arr[each]
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # 2018.07.17 выбираем ID сложного элемента массива
    # ------------------------------------------------------------------------------------------------------------------
    def get_complex_id(gcr_arr, gcr_uuid = None, gcr_name = None):
        ret                                                 =   None
        if(gcr_uuid):
            for each                                        in  gcr_arr:
                if gcr_arr[each].get('uuid')                ==  gcr_uuid:
                    ret                                     =   each
        if(gcr_name):
            for each                                        in  gcr_arr:
                if gcr_arr[each].get('name')                ==  gcr_name:
                    ret                                     =   each
        return ret
    # ------------------------------------------------------------------------------------------------------------------
    # 2020.05.22 получаю номер области основных данных по двум числам
    # ------------------------------------------------------------------------------------------------------------------
    def get_main_area(gma_name, gma_1, gma_2):                                                                          # 1,1
        if gma_1                                            ==  g.execution.c1_dicts.ext_main_id[gma_name]:
            return str(g.execution.c1_dicts.ext_area_main_ids[gma_name][gma_2])
        return '0'
    # ------------------------------------------------------------------------------------------------------------------
    # 2020.05.22 получаю номер области вспомогательных данных по двум числам
    # ------------------------------------------------------------------------------------------------------------------
    def get_add_area(gma_name, gma_1, gma_2):                                                                           # 2,1
        if gma_1                                            ==  g.execution.c1_dicts.ext_add_id[gma_name]:
            return str(g.execution.c1_dicts.ext_area_add_ids[gma_name][gma_2])
        return '0'