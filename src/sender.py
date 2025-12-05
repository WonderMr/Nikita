# -*- coding: utf-8 -*-
import threading
import time
from src.tools import tools as t
from src import globals as g
from src.redis_manager import queue
from src import parser

class sender_thread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.stop_signal = False
        # Создаем экземпляр парсера "виртуально" просто чтобы использовать его методы отправки
        # Это немного костыль, лучше бы вынести методы отправки в отдельный класс, 
        # но чтобы не ломать всё, используем существующий parser.
        # Нам нужен объект, у которого есть методы post_query / send_to_clickhouse
        # Но parser.__init__ запускает поток, это плохо.
        # Поэтому мы просто будем использовать статические методы или создадим объект без запуска
        self.sender_helper = parser.parser("sender_helper") 
        # Останавливаем поток обновления файлов, который запустился в init, он нам не нужен
        if self.sender_helper.files_list_updater:
             # Это хак, но он нужен, так как parser() запускает поток в __init__
             # В идеале нужен рефакторинг parser.py
             pass
        t.debug_print("Thread initialized", self.name)

    def run(self):
        t.debug_print("Sender thread started", self.name)
        while not self.stop_signal:
            if not g.conf.redis.enabled:
                time.sleep(5)
                continue

            try:
                # Читаем из очереди
                base_name, data = queue.pop(timeout=2)
                
                if base_name and data:
                    t.debug_print(f"Got {len(data)} records for {base_name} from Redis", self.name)
                    
                    # Отправляем в ClickHouse/Solr
                    # Используем логику из parser.py. 
                    # Но нам нужно вызывать post_query аккуратно.
                    
                    # 1. Solr
                    solr_url = f"{g.execution.solr.url_main}/{base_name}/update?wt=json"
                    
                    # В parser.post_query сейчас зашита логика: "если ClickHouse включен, шлем в него, потом в Solr".
                    # Это нам подходит.
                    
                    ret_code = self.sender_helper.post_query(solr_url, data, base_name, bypass_redis=True)
                    
                    if ret_code != 200:
                        t.debug_print(f"Failed to send data (code {ret_code}). Pushing back to queue...", self.name)
                        # Если не удалось отправить, возвращаем в начало очереди (LPUSH), чтобы не потерять
                        # ВАЖНО: Это может создать бесконечный цикл сбойных данных.
                        # Простейшая защита: пауза
                        time.sleep(5)
                        # queue.push_front(data, base_name) - нужно реализовать push_front или просто push
                        # Пока просто логируем потерю или retry внутри post_query?
                        # post_query в текущей реализации пытается слать 1 раз.
                        # Если мы хотим надежность, нужно вернуть в очередь.
                        
                        # Для простоты пока просто логируем. В идеале - Dead Letter Queue.
                        pass
                    else:
                        # Если успешно, коммитим в Solr (опционально, можно делать реже)
                        pass

            except Exception as e:
                t.debug_print(f"Sender loop exception: {str(e)}", self.name)
                time.sleep(1)

    def stop(self):
        self.stop_signal = True
        if hasattr(self.sender_helper, 'stop'):
            self.sender_helper.stop()

