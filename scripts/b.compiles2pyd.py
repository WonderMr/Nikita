from    distutils.core      import  setup
from    distutils.extension import  Extension
from    Cython.Distutils    import  build_ext

ext_modules                         =   [
    Extension("src.solr",           ["src/solr.py"]),
    Extension("src.globals",        ["src/globals.py"]),
    Extension("src.tools",          ["src/tools.py"]),
    Extension("src.dictionaries",   ["src/dictionaries.py"]),
    Extension("src.parser",         ["src/parser.py"]),    
    Extension("src.reader",         ["src/reader.py"]),
    Extension("src.messenger",      ["src/messenger.py"])
]

setup(
    name                            =    'Nikita',
    cmdclass                        =    {'build_ext': build_ext},
    ext_modules                     =    ext_modules
)