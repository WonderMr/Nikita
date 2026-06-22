# -*- coding: utf-8 -*-
import  threading                                                                                                       # Stubs for threading
#import  pysolr                                                                                                          # my favorite nonSQL db tool
import  psutil                                                                                                                # psutil is a cross-platform library for retrieving information on running processes and system utilization (CPU, memory, disks, network,sensors) in Python.
import  requests                                                                                                        # Requests HTTP Library
import  subprocess                                                                                                      # Stubs for subprocess
import  time                                                                                                            # Stubs for time
import  shlex                                                                                                           # A lexical analyzer class for simple shell-like syntaxes.
import  os                                                                                                              # OS routines for NT or Posix depending on what system we're on.
import  re                                                                                                              # Regular expressions
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
        if not self.base_exists(cbe_name):
            if not self.base_create(cbe_name):
                t.debug_print("Cannot create Solr core " + cbe_name, self.name)
                return False
        schema_attempts                                     =   3
        for schema_attempt in range(schema_attempts):
            if self.validate_core_schema(cbe_name):
                return True
            if schema_attempt < schema_attempts - 1:
                t.debug_print(
                    f"Solr core {cbe_name} schema validation attempt {schema_attempt + 1}/{schema_attempts} failed, retrying",
                    self.name
                )
                time.sleep(g.waits.solr_on_bad_send_to)
        return False
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        if self.start2():
            for ibase in g.parser.ibases:
                if not self.check_base_exists(ibase[g.nms.ib.name]):
                    t.graceful_shutdown(1)
                    return
        else:
            t.graceful_shutdown(1)
            return
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
    def get_java_major_version(self, java_exe):
        try:
            version_output                                  =   subprocess.check_output(
                                                                    [java_exe, "-version"],
                                                                    stderr=subprocess.STDOUT,
                                                                    text=True
                                                                )
            version_match                                   =   re.search(r'version "([^"]+)"', version_output)
            if not version_match:
                return None
            version                                         =   version_match.group(1)
            if version.startswith("1."):
                return int(version.split(".")[1])
            return int(version.split(".")[0])
        except Exception as e:
            t.debug_print(f"Failed to check Java version for Solr: {e}", self.name)
            return None

    def java_executable_names(self):
        if os.name == "nt":
            return ("java.exe", "java")
        return ("java", "java.exe")

    def get_java_executable(self, java_home):
        for java_name in self.java_executable_names():
            java_exe                                        =   os.path.join(java_home, "bin", java_name)
            if os.path.exists(java_exe):
                return java_exe
        return None

    def start2(self):
        # Solr ВСЕГДА запускается на встроенной Java из подкаталога установки <self_dir>/java
        # (внутри уже лежит bin/java). Системные переменные SOLR_JAVA_HOME / JAVA_HOME
        # намеренно игнорируются — используется только встроенная Java.
        if not g.execution.self_dir:
            t.debug_print("Cannot locate bundled Java: install directory (self_dir) is empty.", self.name)
            return False
        java_home                                           =   os.path.join(g.execution.self_dir, "java")
        java_exe                                            =   self.get_java_executable(java_home)
        if not java_exe:
            t.debug_print(f"Bundled Java not found at {java_home} (expected bin/java). Reinstall with the bundled JDK 17.", self.name)
            return False

        java_major                                          =   self.get_java_major_version(java_exe)
        if java_major is None:
            t.debug_print(f"Cannot detect version of bundled Java: {java_exe}", self.name)
            return False
        if java_major < 17:
            t.debug_print(
                f"Bundled Java is too old: {java_exe} is Java {java_major}, Solr requires Java 17+. "
                "Reinstall with the bundled JDK 17.",
                self.name
            )
            return False

        solr_env                                            =   os.environ.copy()
        solr_env["JAVA_HOME"]                               =   java_home
        solr_env["JRE_HOME"]                                =   java_home
        solr_env["SOLR_JAVA_HOME"]                          =   java_home
        solr_env["PATH"]                                    =   os.path.dirname(java_exe) + os.pathsep + solr_env.get("PATH", "")

        ss_command                                          =   '"'+java_exe+'"'
        ss_command                                          +=  " -server"
        ss_command                                          +=  " -Xms"+g.conf.solr.mem_min
        ss_command                                          +=  " -Xmx"+g.conf.solr.mem_max
        ss_command                                          +=  " -Duser.timezone=UTC"
        ss_command                                          +=  " -XX:+UseG1GC"
        ss_command                                          +=  " -XX:ConcGCThreads="+g.conf.solr.threads
        ss_command                                          +=  " -XX:ParallelGCThreads="+g.conf.solr.threads
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
                                                                    cwd=os.path.join(g.conf.solr.dir, "server"),
                                                                    env=solr_env
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
    def validate_core_schema(self, core_name):
        try:
            field_response                                  =   requests.get(
                                                                    f"{g.execution.solr.url_main}/{core_name}/schema/fields/id",
                                                                    timeout=5
                                                                )
            if field_response.status_code != 200:
                t.debug_print(
                    f"Solr core {core_name} schema id check failed: HTTP {field_response.status_code}",
                    self.name
                )
                return False

            field_type                                      =   field_response.json().get("field", {}).get("type")
            unique_response                                 =   requests.get(
                                                                    f"{g.execution.solr.url_main}/{core_name}/schema/uniquekey",
                                                                    timeout=5
                                                                )
            if unique_response.status_code != 200:
                t.debug_print(
                    f"Solr core {core_name} uniqueKey check failed: HTTP {unique_response.status_code}",
                    self.name
                )
                return False

            unique_key                                      =   unique_response.json().get("uniqueKey")
            if field_type != "string" or unique_key != "id":
                t.debug_print(
                    f"Solr core {core_name} has incompatible schema: id type={field_type}, uniqueKey={unique_key}. "
                    "Recreate the core with the bundled schema before parsing.",
                    self.name
                )
                return False

            return True
        except Exception as e:
            t.debug_print(f"Solr core {core_name} schema validation failed: {e}", self.name)
            return False
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # проверка наличия core среди имеющихся
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def base_exists(self,be_name):
        count                                               =   0
        be_ret                                              =   0
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
