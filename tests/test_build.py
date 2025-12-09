import unittest
import sys
import os
import subprocess
import glob

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestBuild(unittest.TestCase):
    def setUp(self):
        self.root_dir                                       =   os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.src_dir                                        =   os.path.join(self.root_dir, 'src')

    def tearDown(self):
        # Очистка артефактов сборки после тестов
        print("\nCleaning up build artifacts...")
        extensions                                          =   ['*.so', '*.pyd', '*.c', '*.html'] # .html создает cython --annotate
        for ext in extensions:
            for file in glob.glob(os.path.join(self.src_dir, ext)):
                try:
                    os.remove(file)
                    print(f"Removed {file}")
                except OSError as e:
                    print(f"Error removing {file}: {e}")
        
        # Очистка папки build/ если она создалась
        build_dir                                           =   os.path.join(self.root_dir, 'build')
        if os.path.exists(build_dir):
            import shutil
            shutil.rmtree(build_dir, ignore_errors=True)
            print(f"Removed {build_dir}")

    def test_cython_build(self):
        # Запускаем скрипт сборки
        script_path                                         =   os.path.join(self.root_dir, 'scripts', 'b.compiles2pyd.py')
        
        cmd                                                 =   [sys.executable, script_path, "build_ext", "--inplace"]
        
        result                                              =   subprocess.run(
            cmd, 
            cwd=self.root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print("Build stdout:", result.stdout)
            print("Build stderr:", result.stderr)
            
        self.assertEqual(result.returncode, 0, f"Build script failed with return code {result.returncode}")
        
        # Проверяем, что файлы действительно создались (до tearDown)
        # На Linux создаются .so, на Windows .pyd
        # Проверим хотя бы один файл
        generated_files                                     =   glob.glob(os.path.join(self.src_dir, '*.so')) + glob.glob(os.path.join(self.src_dir, '*.pyd'))
        self.assertTrue(len(generated_files) > 0, "No compiled modules found after build")

if __name__ == '__main__':
    unittest.main()
