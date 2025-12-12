# -*- coding: utf-8 -*-
import  threading                                                                                                       # Stubs for threading
#import  pysolr                                                                                                          # my favorite nonSQL db tool
import  psutil                                                                                                                # psutil is a cross-platform library for retrieving information on running processes and system utilization (CPU, memory, disks, network,sensors) in Python.
import  requests                                                                                                        # Requests HTTP Library
import  subprocess                                                                                                      # Stubs for subprocess
import  time                                                                                                            # Stubs for time
import  shlex                                                                                                           # A lexical analyzer class for simple shell-like syntaxes.
import  os                                                                                                              # OS routines for NT or Posix depending on what system we're on.
# ======================================================================================================================
from    src                 import  globals                 as  g
from    src.tools           import  tools                   as  t
# ======================================================================================================================
# ----------------------------------------------------------------------------------------------------------------------
# функции и методы для работы с Apache Solr
# ======================================================================================================================
# ----------------------------------------------------------------------------------------------------------------------
# поток для Solr
# ----------------------------------------------------------------------------------------------------------------------
class solr_thread(threading.Thread):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name                                           =   name
        t.debug_print("Thread initialized", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def check_base_exists(self,cbe_name):
        #for ibase in g.parser.ibases:
        if not (self.base_exists(cbe_name)):                                                                            # если базы нету
            if not self.base_create(cbe_name):                                                                          # то создаём её
                t.debug_print("Не удалось создать ядро " + cbe_name,self.name)
                return False
            else:
                return True
        else:
            return True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        if self.start2():
            for ibase in g.parser.ibases:
                self.check_base_exists(ibase[g.nms.ib.name])
        else:
            t.graceful_shutdown(1)
        t.debug_print("Thread started", self.name)
        g.execution.solr.started                            =   True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        try:
            psutil.Process(g.execution.solr.pid).kill()
        except Exception as e:
            t.debug_print(f"Exception while stopping Solr: {str(e)}", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # запускает Apahe Solr
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def start2(self):
        ss_command                                          =   '"'+g.conf.solr.java_home+'\\bin\\java.exe"'
        ss_command                                          +=  " -server"
        ss_command                                          +=  " -Xms"+g.conf.solr.mem_min
        ss_command                                          +=  " -Xmx"+g.conf.solr.mem_max
        ss_command                                          +=  " -Duser.timezone=UTC"
        ss_command                                          +=  " -XX:NewRatio=3"
        ss_command                                          +=  " -XX:SurvivorRatio=4"
        ss_command                                          +=  " -XX:TargetSurvivorRatio=90"
        ss_command                                          +=  " -XX:MaxTenuringThreshold=8"
        ss_command                                          +=  " -XX:+UseConcMarkSweepGC"
        ss_command                                          +=  " -XX:ConcGCThreads="+g.conf.solr.threads
        ss_command                                          +=  " -XX:ParallelGCThreads="+g.conf.solr.threads
        ss_command                                          +=  " -XX:+CMSScavengeBeforeRemark"
        ss_command                                          +=  " -XX:PretenureSizeThreshold=64m"
        ss_command                                          +=  " -XX:+UseCMSInitiatingOccupancyOnly"
        ss_command                                          +=  " -XX:CMSInitiatingOccupancyFraction=50"
        ss_command                                          +=  " -XX:CMSMaxAbortablePrecleanTime=6000"
        ss_command                                          +=  " -XX:+CMSParallelRemarkEnabled"
        ss_command                                          +=  " -XX:+ParallelRefProcEnabled"
        ss_command                                          +=  " -XX:-OmitStackTraceInFastThrow"
        ss_command                                          +=  ' -XX:+ExitOnOutOfMemoryError'                          # тестово
        #ss_command                                          +=  ' "-Xlog:gc*:file=\\"'                                 # не работает с JRE
        #ss_command                                          +=      g.conf.solr.dir+"\\server\\logs\\solr_gc.log\\"    # не работает с JRE
        #ss_command                                          +=  '":time,uptime:filecount=9,filesize=20000"'            # не работает с JRE
        ss_command                                          +=  " -Xss256k"
        ss_command                                          +=  ' -Dsolr.log.dir="'+g.conf.solr.dir+'\\server\\logs"'
        ss_command                                          +=  ' -Dlog4j.configuration="file:'
        ss_command                                          +=  g.conf.solr.dir+'\\server\\resources\\log4j2.xml"'
        ss_command                                          +=  " -DSTOP.PORT=7983"
        ss_command                                          +=  " -DSTOP.KEY=solrrocks"
        ss_command                                          +=  " -Dsolr.log.muteconsole"
        ss_command                                          +=  ' -Dsolr.solr.home="'+g.conf.solr.dir+'\\server\\solr"'
        ss_command                                          +=  ' -Dsolr.install.dir="'+g.conf.solr.dir+'"'
        ss_command                                          +=  ' -Dsolr.default.confdir="'
        ss_command                                          +=      g.conf.solr.dir+'\\server\\solr\\configsets'
        ss_command                                          +=      '\\_default\\conf"'
        ss_command                                          +=  ' -Djetty.host='+g.conf.solr.listen_interface
        ss_command                                          +=  " -Djetty.port="+g.conf.solr.listen_port
        ss_command                                          +=  ' -Djetty.home="'+g.conf.solr.dir+'\\server"'
        ss_command                                          +=  ' -Djava.io.tmpdir="'+g.conf.solr.dir+'\\server\\tmp"'
        ss_command                                          +=  ' -jar "start.jar"'
        ss_command                                          +=  ' "--module=http" ""'
        args                                                =   shlex.split(ss_command)
        t.debug_print("starting "+ss_command,self.name)
        # эти каталоги нужно создать, если их нету ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        solr_logs_dir                                       =   os.path.join(g.conf.solr.dir, "server", "logs")
        solr_tmp_dir                                        =   os.path.join(g.conf.solr.dir, "server", "tmp")
        
        if not os.path.exists(solr_logs_dir):
            os.makedirs(solr_logs_dir)
        if not os.path.exists(solr_tmp_dir):
            os.makedirs(solr_tmp_dir)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        g.execution.solr.pid                                =   subprocess.Popen(
                                                                    args,
                                                                    cwd=os.path.join(g.conf.solr.dir, "server")
                                                                ).pid
        # запускаю solr и получаю его pid
        solr_wakes                                          =   False
        solr_times                                          =   0
        solr_times_max                                      =   10
        while(not solr_wakes and solr_times<solr_times_max):
            time.sleep(g.conf.solr.wait_after_start)                                                                    # чуть подождём
            try:
                solr_wakes                                  =   requests.get(g.execution.solr.url_main, timeout=5)
            except:
                pass
            solr_times                                      +=  1
        if psutil.pid_exists(g.execution.solr.pid):
            #g.execution.solr.pysorl                         =   pysolr.Solr(g.execution.solr.url_main, timeout = 10)
            return True
        else:
            return False
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # создание нового core
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def base_create(self, bc_name):
        try:
            bc_dir_data                                     =   os.path.join(g.conf.solr.dir, "server", "solr", bc_name, "conf")
            if(not os.path.exists(bc_dir_data)):
                t.debug_print("creating "+bc_dir_data,self.name)
                os.makedirs(bc_dir_data)
            schema                                          =   open(os.path.join(bc_dir_data, "schema.xml"),'w',encoding="UTF8")
            schema.write(g.conf.solr.schema)
            schema.close()
            solrconfig                                      =   open(os.path.join(bc_dir_data, "solrconfig.xml"),'w',encoding="UTF8")
            solrconfig.write(g.conf.solr.config)
            solrconfig.close()
        except Exception as e:
            t.debug_print("Exception while creating core "+bc_name+" "+str(e))
        finally:
            bc_url                                          =   g.execution.solr.url_main\
                                                            +   "/admin/cores?action=CREATE&name="+bc_name\
                                                            +   "&instanceDir="+bc_name\
                                                            +   "&config=solrconfig.xml&dataDir=data"
            bc_ret                                          =   requests.get(bc_url, timeout=10).status_code
        t.debug_print("core "+bc_name+" created with code "+str(bc_ret),self.name)
        return bc_ret                                       ==  200
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # проверка наличия core среди имеющихся
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def base_exists(self,be_name):
        count                                               =   0
        try:
            be_ret                                          =   requests.get(
                                                                    g.execution.solr.url_main \
                                                                    +"/"+be_name+g.conf.solr.ping
                                                                ,timeout=5).status_code
            t.debug_print("core " + be_name + " responds " + str(be_ret), self.name)
        except Exception as e:
            t.debug_print("Solr return "+str(e),self.name)
        while   count < g.waits.solr_cycles \
                and (be_ret if be_ret else 0) not in [200,404]:                                                         # здесь специально для того, если создания ядра сразу не прошло
            time.sleep(g.waits.solr_on_bad_send_to)
            try:
                be_ret                                      =   requests.get(
                                                                    g.execution.solr.url_main
                                                                    +"/"+be_name+g.conf.solr.ping
                                                                ,timeout=5).status_code
                t.debug_print("core " + be_name + " responds " + str(be_ret), self.name)
            except Exception as e:
                t.debug_print("Solr return " + str(e), self.name)
            count                                           +=  1
        return be_ret                                       ==  200
