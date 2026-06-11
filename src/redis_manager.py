# -*- coding: utf-8 -*-
import threading
import psutil
import subprocess
import time
import shlex
import os
import json
from src.tools import tools as t
from src import globals as g

# redis (python) может отсутствовать, если Redis выключен (например, Windows сборка).
try:
    import redis
except Exception:
    redis                                                   =   None

# ----------------------------------------------------------------------------------------------------------------------
# Поток управления процессом Redis Server
# ----------------------------------------------------------------------------------------------------------------------
class redis_thread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name
        t.debug_print("Thread initialized", self.name)

    def run(self):
        if g.conf.redis.enabled and g.conf.redis.server_path:
            self.start_server()
        else:
            t.debug_print("Redis server start skipped (disabled or path not set)", self.name)

    def start_server(self):
        try:
            cmd                                             =   f'"{g.conf.redis.server_path}" --port {g.conf.redis.port}'
            if g.conf.redis.dir:
                cmd                                         +=  f' --dir "{g.conf.redis.dir}"'
            # Добавляем сохранение на диск (RDB) каждые 60 сек если есть 1 изменение
            cmd                                             +=  ' --save 60 1' 
            
            args                                            =   shlex.split(cmd)
            t.debug_print(f"Starting redis: {cmd}", self.name)
            
            # Создаем рабочую директорию если нужно
            if g.conf.redis.dir and not os.path.exists(g.conf.redis.dir):
                os.makedirs(g.conf.redis.dir)

            self.process                                    =   subprocess.Popen(args)
            t.debug_print(f"Redis started with PID {self.process.pid}", self.name)
            
            # Ждем пока процесс жив
            self.process.wait()
        except Exception as e:
            t.debug_print(f"Failed to start Redis server: {e}", self.name)

    def stop(self):
        if hasattr(self, 'process') and self.process:
            t.debug_print("Stopping Redis server...", self.name)
            self.process.terminate()

# ----------------------------------------------------------------------------------------------------------------------
# Класс очереди Redis
# ----------------------------------------------------------------------------------------------------------------------
class RedisQueue:
    def __init__(self):
        self.client                                         =   None
        self.key_prefix                                     =   "nikita:queue:"
        self.main_key                                       =   self.key_prefix + "main"
        self.processing_key                                 =   self.key_prefix + "processing"
        self.dead_key                                       =   self.key_prefix + "dead"
        self.recovery_pending                               =   True
        self.connect(recover=True)

    def connect(self, recover=False):
        if recover:
            self.recovery_pending                           =   True
        if not g.conf.redis.enabled:
            return
        if redis is None:
            t.debug_print("Redis python client module is not available (redis). Redis queue disabled.", "RedisQueue")
            self.client                                     =   None
            return
        try:
            self.client                                     =   redis.Redis(
                host                                        =   g.conf.redis.host,
                port                                        =   int(g.conf.redis.port),
                db                                          =   int(g.conf.redis.db),
                decode_responses                            =   True  # Получаем строки вместо байтов
            )
            self.client.ping()
            if self.recovery_pending:
                if not self.recover_processing():
                    return
                self.recovery_pending                       =   False
            t.debug_print("Connected to Redis", "RedisQueue")
        except Exception as e:
            t.debug_print(f"Redis connection failed: {e}", "RedisQueue")
            self.client                                     =   None

    def recover_processing(self):
        if not self.client:
            return False
        try:
            script                                          =   """
                local payload = redis.call('LPOP', KEYS[1])
                if payload then
                    redis.call('RPUSH', KEYS[2], payload)
                    return 1
                end
                return 0
            """
            while int(self.client.eval(script, 2, self.processing_key, self.main_key)) == 1:
                pass
            return True
        except Exception as e:
            t.debug_print(f"Redis processing recovery failed: {e}", "RedisQueue")
            self.client                                     =   None
            return False

    def push(self, data, base_name):
        """
        Добавляет пакет данных в очередь.
        data: список словарей (записей лога)
        base_name: имя базы данных (для маршрутизации)
        """
        if not self.client:
            self.connect()
            if not self.client:
                return False # Redis недоступен

        try:
            # Сериализуем данные. Можно использовать msgpack для скорости, но json проще для отладки.
            payload                                         =   json.dumps({
                "base":                                         base_name,
                "data":                                         data
            })
            # LPUSH + BRPOPLPUSH дают FIFO и processing-очередь до ack.
            self.client.lpush(self.main_key, payload)
            return True
        except Exception as e:
            t.debug_print(f"Redis push failed: {e}", "RedisQueue")
            self.client                                     =   None # Сбрасываем соединение
            return False

    def pop(self, timeout=5):
        """
        Получает пакет данных из очереди (блокирующий вызов).
        Возвращает (base_name, data, payload) или (None, None, None).
        """
        if not self.client:
            self.connect()
            if not self.client:
                time.sleep(1)
                return None, None, None

        try:
            payload                                         =   self.client.brpoplpush(
                                                                    self.main_key,
                                                                    self.processing_key,
                                                                    timeout=timeout
                                                                )
            if payload:
                try:
                    item                                    =   json.loads(payload)
                    base_name                               =   item["base"]
                    data                                    =   item["data"]
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    t.debug_print(f"Redis payload is invalid, moving to dead letter: {e}", "RedisQueue")
                    if not self.move_to_dead(payload):
                        t.debug_print("Redis invalid payload could not be moved to dead letter", "RedisQueue")
                    return None, None, None
                return base_name, data, payload
        except Exception as e:
            t.debug_print(f"Redis pop failed: {e}", "RedisQueue")
            self.recovery_pending                           =   True
            self.client                                     =   None
        
        return None, None, None

    def ack(self, payload):
        if not payload:
            return False
        if not self.client:
            self.connect()
            if not self.client:
                return False
        try:
            return self.client.lrem(self.processing_key, 1, payload) > 0
        except Exception as e:
            t.debug_print(f"Redis ack failed: {e}", "RedisQueue")
            self.recovery_pending                           =   True
            self.client                                     =   None
            return False

    def requeue(self, payload):
        if not payload:
            return False
        if not self.client:
            self.connect()
            if not self.client:
                return False
        try:
            script                                          =   """
                local removed = redis.call('LREM', KEYS[1], 1, ARGV[1])
                if removed > 0 then
                    redis.call('LPUSH', KEYS[2], ARGV[1])
                    return 1
                end
                return 0
            """
            return int(self.client.eval(script, 2, self.processing_key, self.main_key, payload)) == 1
        except Exception as e:
            t.debug_print(f"Redis requeue failed: {e}", "RedisQueue")
            self.recovery_pending                           =   True
            self.client                                     =   None
            return False

    def move_to_dead(self, payload):
        if not payload:
            return False
        if not self.client:
            self.connect()
            if not self.client:
                return False
        try:
            script                                          =   """
                local removed = redis.call('LREM', KEYS[1], 1, ARGV[1])
                if removed > 0 then
                    redis.call('LPUSH', KEYS[2], ARGV[1])
                    return 1
                end
                return 0
            """
            return int(self.client.eval(script, 2, self.processing_key, self.dead_key, payload)) == 1
        except Exception as e:
            t.debug_print(f"Redis dead-letter move failed: {e}", "RedisQueue")
            self.recovery_pending                           =   True
            self.client                                     =   None
            return False

# Глобальный экземпляр очереди
queue                                                       =   RedisQueue()
