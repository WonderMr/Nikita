# -*- coding: utf-8 -*-
import  cherrypy
import  urllib
import  threading
import  locale
import  json
from    datetime           import  datetime
# ======================================================================================================================
from    src.tools           import  tools                   as  t
from    src                 import  globals                 as  g
from    src                 import  reader                  as  r
# ======================================================================================================================
# собственно, имплементация веб-сервера
# ======================================================================================================================
class journal2ct_web(object):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @cherrypy.expose
    def index(self):
        locale.setlocale(locale.LC_ALL,"")
        
        # Подготовка данных для статистики
        uptime_str                                          =   "Н/Д"
        if g.stats.start_time:
            uptime                                          =   (datetime.now() - g.stats.start_time).total_seconds()
            uptime_str                                      =   f"{int(uptime // 3600)}ч {int((uptime % 3600) // 60)}м {int(uptime % 60)}с"
            
        # Определяем время последней активности (максимум из всех сервисов)
        last_times                                          =   []
        if g.conf.clickhouse.enabled and g.stats.clickhouse_last_success_time:
            last_times.append(g.stats.clickhouse_last_success_time)
        if g.conf.solr.enabled and g.stats.solr_last_success_time:
            last_times.append(g.stats.solr_last_success_time)
        if g.conf.redis.enabled and g.stats.redis_last_success_time:
            last_times.append(g.stats.redis_last_success_time)
            
        last_activity_str                                   =   "Нет данных"
        last_activity_iso                                   =   ""
        if last_times:
            last_max                                        =   max(last_times)
            last_activity_str                               =   last_max.strftime("%H:%M:%S")
            last_activity_iso                               =   last_max.isoformat()

        # ======= Блок статистики (Таблица) ============================================================================
        stats_block                                         =   ""
        stats_block                                         +=  '<div class="stats-container">'
        stats_block                                         +=  '<h2>Статистика сервисов</h2>'
        stats_block                                         +=  '<div class="table stats-table">'
        
        # Заголовки колонок
        stats_block                                         +=  '<div class="row header">'
        stats_block                                         +=  '<span class="cell">Параметр</span>'
        stats_block                                         +=  '<span class="cell">ClickHouse</span>'
        stats_block                                         +=  '<span class="cell">Solr</span>'
        stats_block                                         +=  '<span class="cell">Redis</span>'
        stats_block                                         +=  '</div>'
        
        # Строка Статус
        stats_block                                         +=  '<div class="row">'
        stats_block                                         +=  '<span class="cell parameter">Статус</span>'
        
        # CH Status
        if g.conf.clickhouse.enabled:
            ch_icon                                         =   "🟢" if g.stats.clickhouse_connection_ok else "🔴"
            ch_text                                         =   "Подключено" if g.stats.clickhouse_connection_ok else "Ошибка"
            stats_block                                     +=  f'<span class="cell">{ch_icon} {ch_text}</span>'
        else:
            stats_block                                     +=  '<span class="cell disabled">Отключено</span>'
            
        # Solr Status
        if g.conf.solr.enabled:
            solr_icon                                       =   "🟢" if g.stats.solr_connection_ok else "🔴"
            solr_text                                       =   "Подключено" if g.stats.solr_connection_ok else "Ошибка"
            stats_block                                     +=  f'<span class="cell">{solr_icon} {solr_text}</span>'
        else:
            stats_block                                     +=  '<span class="cell disabled">Отключено</span>'
            
        # Redis Status
        if g.conf.redis.enabled:
            redis_icon                                      =   "🟢" if g.stats.redis_connection_ok else "🔴"
            redis_text                                      =   "Подключено" if g.stats.redis_connection_ok else "Ошибка"
            stats_block                                     +=  f'<span class="cell">{redis_icon} {redis_text}</span>'
        else:
            stats_block                                     +=  '<span class="cell disabled">Отключено</span>'
        stats_block                                         +=  '</div>'
        
        # Строка Хост
        stats_block                                         +=  '<div class="row">'
        stats_block                                         +=  '<span class="cell parameter">Хост</span>'
        stats_block                                         +=  f'<span class="cell">{g.conf.clickhouse.host}:{g.conf.clickhouse.port}</span>' if g.conf.clickhouse.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{g.conf.solr.solr_host}:{g.conf.solr.solr_port}</span>' if g.conf.solr.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{g.conf.redis.host}:{g.conf.redis.port}</span>' if g.conf.redis.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  '</div>'
        
        # Строка База/Core
        stats_block                                         +=  '<div class="row">'
        stats_block                                         +=  '<span class="cell parameter">База / Core / DB</span>'
        stats_block                                         +=  f'<span class="cell">{g.conf.clickhouse.database}</span>' if g.conf.clickhouse.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">default</span>' if g.conf.solr.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{g.conf.redis.db}</span>' if g.conf.redis.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  '</div>'
        
        # Строка Отправлено/В очереди
        stats_block                                         +=  '<div class="row">'
        stats_block                                         +=  '<span class="cell parameter">Записей</span>'
        stats_block                                         +=  f'<span class="cell">{locale.format("%d", g.stats.clickhouse_total_sent, grouping=True)}</span>' if g.conf.clickhouse.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{locale.format("%d", g.stats.solr_total_sent, grouping=True)}</span>' if g.conf.solr.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{locale.format("%d", g.stats.redis_total_queued, grouping=True)}</span>' if g.conf.redis.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  '</div>'
        
        # Строка Ошибок
        stats_block                                         +=  '<div class="row">'
        stats_block                                         +=  '<span class="cell parameter">Ошибок</span>'
        stats_block                                         +=  f'<span class="cell">{g.stats.clickhouse_total_errors}</span>' if g.conf.clickhouse.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{g.stats.solr_total_errors}</span>' if g.conf.solr.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  f'<span class="cell">{g.stats.redis_total_errors}</span>' if g.conf.redis.enabled else '<span class="cell">-</span>'
        stats_block                                         +=  '</div>'
        
        stats_block                                         +=  '</div>' # end table
        
        # Последние ошибки (глобальные)
        if g.stats.last_errors:
            stats_block                                     +=  '<div class="errors-list" style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;">'
            stats_block                                     +=  '<h3>🚨 Последние ошибки</h3>'
            for error_time, error_type, error_msg in reversed(g.stats.last_errors[-3:]):
                error_iso                                   =   error_time.isoformat()
                stats_block                                 +=  '<div class="stats-row error" style="font-size: 0.9em;">'
                stats_block                                 +=  f'<span class="stats-label">[<span class="time-val" data-ts="{error_iso}">{error_time.strftime("%H:%M:%S")}</span>] {error_type}:</span>'
                stats_block                                 +=  f'<span class="stats-value">{error_msg[:120]}</span>'
                stats_block                                 +=  '</div>'
            stats_block                                     +=  '</div>'
            
        stats_block                                         +=  '</div>' # end stats-container

        
        # ======= Блок обрабатываемых баз ==============================================================================
        bases                                               =   ""
        bases                                               +=  '<div class="table-container">'
        bases                                               +=  '<h2>Обрабатываемые базы</h2>'
        bases                                               +=  '<div class="table">'
        bases                                               +=  '<div class="row header">'
        bases                                               +=  '<span class="cell">Название базы</span>'
        bases                                               +=  '<span class="cell">Путь к журналу регистрации</span>'
        bases                                               +=  '<span class="cell">Тип ЖР</span>'
        bases                                               +=  '<span class="cell">Размер ЖР</span>'
        bases                                               +=  '<span class="cell">Обработано</span>'
        bases                                               +=  '<span class="cell">% Обработано</span>'
        bases                                               +=  '</div>'

        for base in g.parser.ibases:
            base_total                                      =   base[g.nms.ib.total_size]\
                                                                if base[g.nms.ib.total_size]>=base[g.nms.ib.parsed_size]\
                                                                else base[g.nms.ib.parsed_size]
            jr_format                                       =   base[g.nms.ib.jr_format]
            is_lgf                                          =   jr_format == 'lgf'
            
            bases                                           +=  '<div class="row" onclick="colorize(this)">'
            bases                                           +=  '<span class="cell"">'                          \
                                                            +   t.denormalize_ib_name(base[g.nms.ib.name])      \
                                                            +   "</span>"
            bases                                           +=  '<span class="cell">'                           \
                                                            +   base[g.nms.ib.jr_dir]                           \
                                                            +   "</span>"
            bases                                           +=  '<span class="cell">'                           \
                                                            +   jr_format                                       \
                                                            +   "</span>"
            
            # Размер ЖР с data-атрибутами для JS конвертации
            bases                                           +=  '<span class="cell size-value" data-val="' + str(base_total) + '" data-type="' + jr_format + '">' \
                                                            +   locale.format(
                                                                    '%d',
                                                                    base_total,
                                                                    grouping        =   True,
                                                                    monetary        =   True
                                                                )                                               \
                                                            +   (' байт' if is_lgf else ' шт.')                 \
                                                            +   "</span>"
            
            # Обработано с data-атрибутами
            bases                                           +=  '<span class="cell size-value" data-val="' + str(base[g.nms.ib.parsed_size]) + '" data-type="' + jr_format + '">' \
                                                            +   locale.format(
                                                                    '%d',
                                                                    base[g.nms.ib.parsed_size],
                                                                    grouping        =   True,
                                                                    monetary        =   True
                                                                )                                               \
                                                            +   (' байт' if is_lgf else ' шт.')                 \
                                                            +   "</span>"
                                                            
            bases                                           +=  '<span class="cell">'                           \
                                                            +   str(
                                                                    round(
                                                                        (
                                                                            base[g.nms.ib.parsed_size]/
                                                                            (
                                                                                int(base_total)
                                                                                if int(base_total) > 0
                                                                                else 1
                                                                            )*100
                                                                        ),
                                                                        4
                                                                    )
                                                                )                                               \
                                                            +   "</span>"
            bases                                           +=  '</div>'
        
        bases                                               +=  '</div>'
        bases                                               +=  '</div>'
        
        # ======= Верхняя панель (Controls + Info) =====================================================================
        top_bar                                             =   ""
        top_bar                                             +=  '<div class="refresh-controls">'
        
        # Left: Refresh & Units & Timezone
        top_bar                                             +=  '<div style="display: flex; align-items: center; flex-wrap: wrap;">'
        
        # Refresh
        top_bar                                             +=  '<div style="display: flex; align-items: center; margin-right: 20px;">'
        top_bar                                             +=  '<span>🔄 Автообновление:</span>'
        top_bar                                             +=  '<label class="switch">'
        top_bar                                             +=  '<input type="checkbox" id="autoRefresh">'
        top_bar                                             +=  '<span class="slider round"></span>'
        top_bar                                             +=  '</label>'
        top_bar                                             +=  '<input type="number" id="refreshInterval" value="30" min="5" style="width: 50px; margin-left: 5px;">'
        top_bar                                             +=  '<span style="margin-left: 5px;">сек.</span>'
        top_bar                                             +=  '</div>'

        # Timezone
        top_bar                                             +=  '<div style="display: flex; align-items: center; margin-right: 20px;">'
        top_bar                                             +=  '<span>🕒 Пояс: GMT</span>'
        top_bar                                             +=  '<select id="timezoneSelect" style="margin-left: 5px; padding: 2px 5px; border: 1px solid #ccc; border-radius: 4px;">'
        top_bar                                             +=  '<option value="0">+0</option>'
        top_bar                                             +=  '<option value="1">+1</option>'
        top_bar                                             +=  '<option value="2">+2</option>'
        top_bar                                             +=  '<option value="3" selected>+3</option>'
        top_bar                                             +=  '<option value="4">+4</option>'
        top_bar                                             +=  '<option value="5">+5</option>'
        top_bar                                             +=  '<option value="6">+6</option>'
        top_bar                                             +=  '<option value="7">+7</option>'
        top_bar                                             +=  '<option value="8">+8</option>'
        top_bar                                             +=  '</select>'
        top_bar                                             +=  '</div>'

        # Units
        top_bar                                             +=  '<div class="units-controls" style="display: flex; align-items: center;">'
        top_bar                                             +=  '<span style="margin-right: 10px;">Единицы:</span>'
        top_bar                                             +=  '<div class="btn-group">'
        top_bar                                             +=  '<button class="unit-btn active" data-unit="auto">Auto</button>'
        top_bar                                             +=  '<button class="unit-btn" data-unit="KB">KB</button>'
        top_bar                                             +=  '<button class="unit-btn" data-unit="MB">MB</button>'
        top_bar                                             +=  '<button class="unit-btn" data-unit="GB">GB</button>'
        top_bar                                             +=  '</div>'
        top_bar                                             +=  '</div>'
        
        top_bar                                             +=  '</div>' # End Left
        
        # Right: Uptime & Last Activity
        top_bar                                             +=  '<div style="display: flex; align-items: center; margin-left: auto; font-size: 0.9em; color: #555;">'
        top_bar                                             +=  f'<span style="margin-right: 20px;">⏱ Время работы: <b>{uptime_str}</b></span>'
        if last_activity_iso:
            top_bar                                         +=  f'<span>🚀 Последняя отправка: <b><span class="time-val" data-ts="{last_activity_iso}">{last_activity_str}</span></b></span>'
        else:
            top_bar                                         +=  f'<span>🚀 Последняя отправка: <b>{last_activity_str}</b></span>'
        top_bar                                             +=  '</div>'
        
        top_bar                                             +=  '</div>'

        return \
            """
            <html>
            <head>
                <meta charset="utf-8">
                <title>Панель управления службой индексации журналов регистрации</title>
                <style type="text/css">
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 10px;
                        background-color: #f5f5f5;
                        color: #333;
                    }
                    h1 {
                        color: #00b36b;
                        font-size: 20px;
                        margin-bottom: 15px;
                    }
                    h2 {
                        color: #333;
                        margin-bottom: 10px;
                        border-bottom: 2px solid #00b36b;
                        padding-bottom: 5px;
                        font-size: 18px;
                    }
                    h3 {
                        color: #555;
                        margin: 5px 0;
                        font-size: 16px;
                    }
                    .stats-container, .table-container, .refresh-controls {
                        background: white;
                        padding: 10px 15px;
                        margin-bottom: 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    }
                    .refresh-controls {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 10px 20px;
                        flex-wrap: wrap;
                    }
                    .stats-table .row {
                        display: grid;
                        grid-template-columns: 150px 1fr 1fr 1fr;
                        border-bottom: 1px solid #eee;
                    }
                    .stats-table .row.header {
                        font-weight: bold;
                        background-color: #00b36b;
                        color: white;
                        border-bottom: 2px solid #00995c;
                    }
                    .stats-table .cell {
                        padding: 8px 10px;
                        display: flex;
                        align-items: center;
                    }
                    .stats-table .cell.parameter {
                        font-weight: 600;
                        background-color: #f9f9f9;
                        border-right: 1px solid #eee;
                    }
                    .stats-table .cell.disabled {
                        color: #999;
                        font-style: italic;
                    }
                    
                    .stats-row.error {
                        background-color: #fff3cd;
                        padding: 5px 10px;
                        margin: 2px 0;
                        border-radius: 4px;
                        border-left: 3px solid #ff6b6b;
                        display: flex;
                        justify-content: space-between;
                    }
                    
                    .table {
                        display: table;
                        border-collapse: separate;
                        border-spacing: 0;
                        width: 100%;
                        border: 1px solid #eee;
                        border-radius: 4px;
                        overflow: hidden;
                    }
                    .row {
                        display: table-row;
                        cursor: pointer;
                        transition: background-color 0.2s;
                    }
                    .row.header {
                        font-weight: bold;
                        background-color: #00b36b;
                        color: white;
                    }
                    .cell {
                        display: table-cell;
                        padding: 8px 10px;
                        border-bottom: 1px solid #eee;
                        text-align: left;
                        background-color: white;
                    }
                    .row.header .cell {
                        border-bottom: 2px solid #00995c;
                        text-transform: uppercase;
                        font-size: 12px;
                        letter-spacing: 0.5px;
                        background-color: #00b36b;
                    }
                    .row:not(.header):hover .cell {
                        background-color: #f0f9f4;
                    }
                    
                    /* Switch toggle styles */
                    .switch {
                        position: relative;
                        display: inline-block;
                        width: 34px;
                        height: 20px;
                        margin: 0 8px;
                    }
                    .switch input { 
                        opacity: 0;
                        width: 0;
                        height: 0;
                    }
                    .slider {
                        position: absolute;
                        cursor: pointer;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background-color: #ccc;
                        transition: .4s;
                        border-radius: 34px;
                    }
                    .slider:before {
                        position: absolute;
                        content: "";
                        height: 14px;
                        width: 14px;
                        left: 3px;
                        bottom: 3px;
                        background-color: white;
                        transition: .4s;
                        border-radius: 50%;
                    }
                    input:checked + .slider {
                        background-color: #00b36b;
                    }
                    input:checked + .slider:before {
                        transform: translateX(14px);
                    }
                    
                    /* Unit buttons styles */
                    .btn-group {
                        display: flex;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        overflow: hidden;
                    }
                    .unit-btn {
                        background-color: #f8f9fa;
                        border: none;
                        border-right: 1px solid #ccc;
                        padding: 4px 8px;
                        cursor: pointer;
                        font-size: 13px;
                        transition: background-color 0.2s;
                    }
                    .unit-btn:last-child {
                        border-right: none;
                    }
                    .unit-btn:hover {
                        background-color: #e2e6ea;
                    }
                    .unit-btn.active {
                        background-color: #00b36b;
                        color: white;
                    }
                </style>   
                <script type="text/javascript">
                    function colorize(Element) {
                        elements = document.querySelectorAll(".table .row:not(.header) .cell");  
                        if(elements.length > 0){
                            for(var i = 0; i < elements.length; i++){
                                if(!elements[i].classList.contains('parameter')) {
                                    elements[i].style.backgroundColor = 'white';
                                    elements[i].style.color = 'inherit';
                                }
                            }
                        }
                        
                        var children = Element.children;
                        for (var i = 0; i < children.length; i++) {
                             if(!children[i].classList.contains('parameter')) {
                                children[i].style.backgroundColor = '#00b36b';
                                children[i].style.color = 'white';
                             }
                        }
                        return false;
                    }
                    
                    // Форматирование размера
                    function formatSize(value, unit) {
                        const val = parseFloat(value);
                        if (isNaN(val)) return value;
                        
                        if (unit === 'KB') return (val / 1024).toFixed(2) + ' KB';
                        if (unit === 'MB') return (val / (1024 * 1024)).toFixed(2) + ' MB';
                        if (unit === 'GB') return (val / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
                        
                        // Auto
                        if (val < 1024) return val + ' Б';
                        if (val < 1024 * 1024) return (val / 1024).toFixed(2) + ' KB';
                        if (val < 1024 * 1024 * 1024) return (val / (1024 * 1024)).toFixed(2) + ' MB';
                        return (val / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
                    }

                    // Обновление всех ячеек с размерами
                    function updateSizes(unit) {
                        const cells = document.querySelectorAll('.size-value');
                        cells.forEach(cell => {
                            const type = cell.getAttribute('data-type');
                            const val = cell.getAttribute('data-val');
                            
                            if (type === 'lgf') {
                                cell.textContent = formatSize(val, unit);
                            }
                        });
                    }
                    
                    // Форматирование времени с учетом пояса
                    function updateTimes(offset) {
                        document.querySelectorAll('.time-val').forEach(el => {
                            const ts = el.getAttribute('data-ts');
                            if (!ts) return;
                            
                            // Считаем, что серверное время - это UTC, если в строке нет зоны
                            // Если ISO строка без Z, добавляем Z для корректного парсинга как UTC
                            const timeStr = ts.endsWith('Z') ? ts : ts + 'Z';
                            const date = new Date(timeStr);
                            
                            if (isNaN(date.getTime())) return;
                            
                            // Прибавляем смещение (в часах)
                            // getTime() дает миллисекунды
                            const targetTime = new Date(date.getTime() + (offset * 3600000));
                            
                            const hours = targetTime.getUTCHours().toString().padStart(2, '0');
                            const minutes = targetTime.getUTCMinutes().toString().padStart(2, '0');
                            const seconds = targetTime.getUTCSeconds().toString().padStart(2, '0');
                            
                            el.textContent = hours + ':' + minutes + ':' + seconds;
                        });
                    }

                    document.addEventListener("DOMContentLoaded", function() {
                        // --- Автообновление ---
                        const checkbox = document.getElementById('autoRefresh');
                        const intervalInput = document.getElementById('refreshInterval');
                        let timer = null;

                        const savedState = localStorage.getItem('nikita_autoRefresh');
                        if (savedState) {
                            const state = JSON.parse(savedState);
                            checkbox.checked = state.enabled;
                            intervalInput.value = state.interval;
                        } else {
                            checkbox.checked = true;
                            intervalInput.value = 30;
                        }

                        function saveRefreshState() {
                            localStorage.setItem('nikita_autoRefresh', JSON.stringify({
                                enabled: checkbox.checked,
                                interval: intervalInput.value
                            }));
                        }

                        function updateTimer() {
                            if (timer) clearTimeout(timer);
                            saveRefreshState();
                            if (checkbox.checked) {
                                const interval = parseInt(intervalInput.value) || 30;
                                const ms = interval * 1000;
                                if (ms >= 1000) {
                                    timer = setTimeout(() => location.reload(), ms);
                                }
                            }
                        }

                        checkbox.addEventListener('change', updateTimer);
                        intervalInput.addEventListener('change', updateTimer);
                        updateTimer();
                        
                        // --- Единицы измерения ---
                        const unitBtns = document.querySelectorAll('.unit-btn');
                        let currentUnit = localStorage.getItem('nikita_unit') || 'auto';
                        
                        unitBtns.forEach(btn => {
                            if (btn.getAttribute('data-unit') === currentUnit) {
                                btn.classList.add('active');
                            } else {
                                btn.classList.remove('active');
                            }
                            
                            btn.addEventListener('click', function() {
                                currentUnit = this.getAttribute('data-unit');
                                localStorage.setItem('nikita_unit', currentUnit);
                                
                                unitBtns.forEach(b => b.classList.remove('active'));
                                this.classList.add('active');
                                
                                updateSizes(currentUnit);
                            });
                        });
                        updateSizes(currentUnit);
                        
                        // --- Часовой пояс ---
                        const tzSelect = document.getElementById('timezoneSelect');
                        // По умолчанию GMT+3
                        let currentOffset = localStorage.getItem('nikita_timezone');
                        if (currentOffset === null) {
                            currentOffset = "3";
                        }
                        
                        tzSelect.value = currentOffset;
                        
                        tzSelect.addEventListener('change', function() {
                            const offset = parseInt(this.value);
                            localStorage.setItem('nikita_timezone', offset);
                            updateTimes(offset);
                        });
                        
                        // Инициализация времени
                        updateTimes(parseInt(currentOffset));
                    });
                </script>
            </head>
            <body>
                <h1>📊 Nikita - Панель мониторинга</h1>
                """+top_bar+"""
                """+stats_block+"""
                """+bases+"""
            </body>
            </html>                    
            """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @cherrypy.expose
    def query(self):
        return "Hello World!"
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @cherrypy.expose
    def stats_api(self):
        """API endpoint для получения статистики в JSON формате"""
        cherrypy.response.headers['Content-Type']           =   'application/json; charset=utf-8'
        
        stats_data                                          =   {}
        
        # Общая информация
        if g.stats.start_time:
            uptime                                          =   (datetime.now() - g.stats.start_time).total_seconds()
            stats_data['uptime_seconds']                    =   uptime
            stats_data['uptime_formatted']                  =   f"{int(uptime // 3600)}ч {int((uptime % 3600) // 60)}м {int(uptime % 60)}с"
        else:
            stats_data['uptime_seconds']                    =   0
            stats_data['uptime_formatted']                  =   "Н/Д"
        
        stats_data['total_records_parsed']                  =   g.stats.total_records_parsed
        
        # ClickHouse
        if g.conf.clickhouse.enabled:
            stats_data['clickhouse']                        =   {
                                                                    'enabled'           :   True,
                                                                    'host'              :   g.conf.clickhouse.host,
                                                                    'port'              :   g.conf.clickhouse.port,
                                                                    'database'          :   g.conf.clickhouse.database,
                                                                    'connection_ok'     :   g.stats.clickhouse_connection_ok,
                                                                    'total_sent'        :   g.stats.clickhouse_total_sent,
                                                                    'total_errors'      :   g.stats.clickhouse_total_errors,
                                                                    'last_success_time' :   g.stats.clickhouse_last_success_time.isoformat() if g.stats.clickhouse_last_success_time else None,
                                                                    'last_error_time'   :   g.stats.clickhouse_last_error_time.isoformat() if g.stats.clickhouse_last_error_time else None,
                                                                    'last_error_msg'    :   g.stats.clickhouse_last_error_msg
                                                                }
        else:
            stats_data['clickhouse']                        =   {'enabled': False}
        
        # Solr
        if g.conf.solr.enabled:
            stats_data['solr']                              =   {
                                                                    'enabled'           :   True,
                                                                    'host'              :   g.conf.solr.solr_host,
                                                                    'port'              :   g.conf.solr.solr_port,
                                                                    'connection_ok'     :   g.stats.solr_connection_ok,
                                                                    'total_sent'        :   g.stats.solr_total_sent,
                                                                    'total_errors'      :   g.stats.solr_total_errors,
                                                                    'last_success_time' :   g.stats.solr_last_success_time.isoformat() if g.stats.solr_last_success_time else None,
                                                                    'last_error_time'   :   g.stats.solr_last_error_time.isoformat() if g.stats.solr_last_error_time else None,
                                                                    'last_error_msg'    :   g.stats.solr_last_error_msg
                                                                }
        else:
            stats_data['solr']                              =   {'enabled': False}
        
        # Redis
        if g.conf.redis.enabled:
            stats_data['redis']                             =   {
                                                                    'enabled'           :   True,
                                                                    'host'              :   g.conf.redis.host,
                                                                    'port'              :   g.conf.redis.port,
                                                                    'connection_ok'     :   g.stats.redis_connection_ok,
                                                                    'total_queued'      :   g.stats.redis_total_queued,
                                                                    'total_errors'      :   g.stats.redis_total_errors,
                                                                    'last_success_time' :   g.stats.redis_last_success_time.isoformat() if g.stats.redis_last_success_time else None,
                                                                    'last_error_time'   :   g.stats.redis_last_error_time.isoformat() if g.stats.redis_last_error_time else None,
                                                                    'last_error_msg'    :   g.stats.redis_last_error_msg
                                                                }
        else:
            stats_data['redis']                             =   {'enabled': False}
        
        # Последние ошибки
        stats_data['last_errors']                           =   []
        for error_time, error_type, error_msg in reversed(g.stats.last_errors[-10:]):
            stats_data['last_errors'].append({
                                                                    'time'      :   error_time.isoformat(),
                                                                    'type'      :   error_type,
                                                                    'message'   :   error_msg
                                                                })
        
        # Информация о базах
        stats_data['databases']                             =   []
        for base in g.parser.ibases:
            base_total                                      =   base[g.nms.ib.total_size] if base[g.nms.ib.total_size] >= base[g.nms.ib.parsed_size] else base[g.nms.ib.parsed_size]
            percent                                         =   round((base[g.nms.ib.parsed_size] / (int(base_total) if int(base_total) > 0 else 1)) * 100, 4)
            
            stats_data['databases'].append({
                                                                    'name'          :   t.denormalize_ib_name(base[g.nms.ib.name]),
                                                                    'path'          :   base[g.nms.ib.jr_dir],
                                                                    'format'        :   base[g.nms.ib.jr_format],
                                                                    'total_size'    :   base_total,
                                                                    'parsed_size'   :   base[g.nms.ib.parsed_size],
                                                                    'percent'       :   percent
                                                                })
        
        return json.dumps(stats_data, ensure_ascii=False, indent=2)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @cherrypy.expose
    def show(self, length=9):
        fail_on                                            =    "start"
        try:
            t.debug_print("got query","cherry")
            fail_on                                         =   "post_size"
            post_size                                       =   cherrypy.request.headers['Content-Length']              # получаю размер post-запроса
            fail_on                                         =   "post_rawbody"
            post_rawbody                                    =   cherrypy.request.body.read(int(post_size))              # читаю сам запрос
            fail_on                                         =   "post_decoded"
            post_decoded                                    =   urllib.parse.unquote(post_rawbody.decode("utf-8"))      # декодирую текст запроса
            #if(post_decoded):
            fail_on                                         =   "show_return"
            show_return                                     =   r.reader.full_proceess_read(post_decoded)
            t.debug_print("data send", "cherry")
            #else:
            #    show_return                                =   "Request not received"
        except Exception as e:
            t.debug_print("query exception "+fail_on+":"+str(e), "cherry")
            show_return                                     =   "Exception8 "+str(e)
        return show_return;
    index.exposed                                           =   True
# ======================================================================================================================
# поток, в котором работает http-сервер
# ======================================================================================================================
class cherry_thread(threading.Thread):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name
        t.debug_print("Thread initialized", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        try:
            t.debug_print(f"Настройка CherryPy веб-сервера...", self.name)
            t.debug_print(f"Интерфейс: {g.conf.http.listen_interface}", self.name)
            t.debug_print(f"Порт: {g.conf.http.listen_port}", self.name)
            
            cherrypy.config.update({'server.socket_host'        :   g.conf.http.listen_interface})
            cherrypy.config.update({'server.socket_port'        :   int(g.conf.http.listen_port)})
            cherrypy.config.update({'log.screen'                :   False})
            
            t.debug_print(f"✓ CherryPy запущен на http://{g.conf.http.listen_interface}:{g.conf.http.listen_port}/", self.name)
            t.debug_print(f"✓ Веб-панель мониторинга: http://{g.conf.http.listen_interface}:{g.conf.http.listen_port}/", self.name)
            t.debug_print(f"✓ JSON API статистики: http://{g.conf.http.listen_interface}:{g.conf.http.listen_port}/stats_api", self.name)
            
            cherrypy.quickstart(journal2ct_web())
        except Exception as e:
            t.debug_print(f"✗ Ошибка запуска CherryPy: {str(e)}", self.name)
            import traceback
            t.debug_print(f"✗ Traceback:\n{traceback.format_exc()}", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        t.debug_print("Останавливаем CherryPy веб-сервер...", self.name)
        cherrypy.engine.exit()
        t.debug_print("✓ CherryPy остановлен", self.name)
# ======================================================================================================================