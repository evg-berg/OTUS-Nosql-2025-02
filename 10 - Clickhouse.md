1. Устанавливаем Clickhouse
   ```sh
   sudo apt-get install -y apt-transport-https ca-certificates dirmngr && sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 8919F6BD2B48D754 && echo "deb https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list && sudo apt-get update && sudo apt-get install -y clickhouse-server clickhouse-client
   ```
   Запускаем
   ```sh
   sudo service clickhouse-server start
   ```
   И проверяем
   ```sh
   sudo service clickhouse-server status
   ```
3. Устанавливаем gsutil
   ```sh
   curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
   tar -xf google-cloud-cli-linux-x86_64.tar.gz
   ./google-cloud-sdk/install.sh
   ```
4. Скачиваем тестовые данные
   ```sh
   mkdir ./taxi_data
   gsutil -m cp -R gs://chicago10/taxi.csv.0000000000[0-3]* ./taxi_data/
   ```
5. Подключаемся к серверу, предварительно удалив (для целей тестирования) файл с паролем по умолчанию
   ```sh
   sudo rm /etc/clickhouse-server/users.d/default-password.xml
   clickhouse-client
   ```
7. Смотрим БД
   ```clickhouse
   show databases;
   ```
9. 
