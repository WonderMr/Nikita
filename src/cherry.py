# -*- coding: utf-8 -*-
import  cherrypy
import  urllib
import  threading
import  locale
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
        bases                                               =   ""
        bases                                               +=  '<div class="row"><span></span>'
        bases                                               +=  '<span class="cell">Обрабатываемые базы</span>'
        bases                                               +=  '<span></span></div>'
        bases                                               +=  '<div class="row">'
        bases                                               +=  '<span class="cell">Название базы</span>'
        bases                                               +=  '<span class="cell">Путь к журналу регистрации</span>'
        bases                                               +=  '<span class="cell">Тип ЖР</span>'
        bases                                               +=  '<span class="cell">Размер ЖР (байт или записей)</span>'
        bases                                               +=  '<span class="cell">Обработано(байт или записей)</span>'
        bases                                               +=  '<span class="cell">% Обработано</span>'
        bases                                               +=  '</div>'

        for base in g.parser.ibases:
            base_total                                      =   base[g.nms.ib.total_size]\
                                                                if base[g.nms.ib.total_size]>=base[g.nms.ib.parsed_size]\
                                                                else base[g.nms.ib.parsed_size]                         # решил починить отображение таким незамысловатым образом https://github.com/WonderMr/Journal2Ct/issues/40
            bases                                           +=  '<div class="row" onclick="colorize(this)">'
            bases                                           +=  '<span class="cell"">'                          \
                                                            +   t.denormalize_ib_name(base[g.nms.ib.name])      \
                                                            +   "</span>"
            bases                                           +=  '<span class="cell">'                           \
                                                            +   base[g.nms.ib.jr_dir]                           \
                                                            +   "</span>"
            bases                                           +=  '<span class="cell">'                           \
                                                            +   base[g.nms.ib.jr_format]                        \
                                                            +   "</span>"
            bases                                           +=  '<span class="cell">'                           \
                                                            +   locale.format(
                                                                    '%d',
                                                                    base_total,
                                                                    grouping        =   True,
                                                                    monetary        =   True
                                                                )                                               \
                                                            +   "</span>"
            bases                                           +=  '<span class="cell">'                           \
                                                            +   locale.format(
                                                                    '%d',
                                                                    base[g.nms.ib.parsed_size],
                                                                    grouping        =   True,
                                                                    monetary        =   True
                                                                )                                               \
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
            #bases                                           +=  '<span class="cell"><button>Перестроить</button></span>'
            bases                                           +=  '</div>'
        return \
            """
            <html>
            <title>Панель управления службой индексации журналов регистрации</title>

            <style type="text/css">
                .table {display:table;border-collapse:separate;border-spacing:5px; cursor: default;}
                .row {display:table-row; cursor: default;}
                .cell {display:table-cell;padding:5px;border:1px solid black; cursor: default;}
            </style>   
            <script type="text/javascript">
                function colorize(Element) {
                    elements	= document.getElementsByClassName("row");  
                    if(elements.length>0){
  	                    for(var i = 0; i < elements.length; i++){
    	                    elements.item(i).style.backgroundColor = 'white';
  	                    }
                    }
	                Element.style.backgroundColor = '#00b36b';
	                return false;
                }
            </script>
            <body>
            <div class="table">"""+bases+"""</div>
            <body>
            </html>                    
            """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @cherrypy.expose
    def query(self):
        return "Hello World!"
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
        cherrypy.config.update({'server.socket_host'        :   g.conf.http.listen_interface})
        cherrypy.config.update({'server.socket_port'        :   int(g.conf.http.listen_port)})
        cherrypy.quickstart(journal2ct_web())
        t.debug_print("Thread started", self.name)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def stop(self):
        cherrypy.engine.stop()
# ======================================================================================================================