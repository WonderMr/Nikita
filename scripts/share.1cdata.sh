cd "$(dirname "$0")/.."
sudo groupadd 1c_data_group
sudo usermod -aG 1c_data_group wondermr
sudo chgrp -R 1c_data_group /home/usr1cv8/.1cv8/1C/1cv8/regs_1541
sudo chgrp -R 1c_data_group /home/usr1cv8/.1cv8/1C/1cv8/
sudo chgrp -R 1c_data_group /home/usr1cv8/.1cv8/1C
sudo chgrp -R 1c_data_group /home/usr1cv8/.1cv8
sudo chgrp -R 1c_data_group /home/usr1cv8
sudo chmod -R 750 /home/usr1cv8/.1cv8/1C/1cv8/regs_1541
sudo chmod -R 750 /home/usr1cv8/.1cv8/1C/1cv8/
sudo chmod g+x /home/usr1cv8/.1cv8/1C
sudo chmod g+x /home/usr1cv8/.1cv8
sudo chmod g+x /home/usr1cv8