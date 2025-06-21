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
6. Смотрим БД
   ```clickhouse
   otus-nosql.ru-central1.internal :) show databases;
   SHOW DATABASES
   Query id: 7b789890-f245-467d-8117-df8fa31b84f6
      ┌─name───────────────┐
   1. │ INFORMATION_SCHEMA │
   2. │ default            │
   3. │ information_schema │
   4. │ system             │
      └────────────────────┘
   4 rows in set. Elapsed: 0.002 sec.
   ```
7. Создадим базу данных taxi
   ```clickhouse
   CREATE DATABASE IF NOT EXISTS taxi
   CREATE TABLE taxi.taxi_trips
   (
    `unique_key` String,
    `taxi_id` String,
    `trip_start_timestamp` DateTime,
    `trip_end_timestamp` DateTime,
    `trip_seconds` Int64,
    `trip_miles` Decimal(10, 4),
    `pickup_census_tract` String,
    `dropoff_census_tract` String,
    `pickup_community_area` String,
    `dropoff_community_area` String,
    `fare` Decimal(10, 4),
    `tips` Decimal(10, 4),
    `tolls` Decimal(10, 4),
    `extras` Decimal(10, 4),
    `trip_total` Decimal(10, 4),
    `payment_type` String,
    `company` String,
    `pickup_latitude` Decimal(10, 4),
    `pickup_longitude` Decimal(10, 4),
    `pickup_location` String,
    `dropoff_latitude` Decimal(10, 4),
    `dropoff_longitude` Decimal(10, 4),
    `dropoff_location` String
   )
   ENGINE = MergeTree
   PARTITION BY toYYYYMM(trip_start_timestamp)
   ORDER BY (payment_type, tips, tolls)
   ```
8. Готовим исходные данные для загрузки - убираем "UTC" из файлов .csv
   ```sh
   cd ./taxi_data
   mcedit crop_utc
   #!/bin/bash
   for i in *; do
    if [ "${i:0:4}" = "taxi" ];then
        echo "Готовим файл  $i"
        awk '{gsub(/ UTC,/,",")}1' $i > temp.txt && mv temp.txt $i
        tail -n3 $i
    fi
   done
   chmod +x crop_utc
   ./crop_utc
   ```
9. Загружаем данные в БД
   ```sh
   mcedit insert_data
   #!/bin/bash
   for i in *; do
      if [ "${i:0:4}" = "taxi" ];then
        echo "Вставляем данные из файла  $i"
        cat $i | clickhouse-client --query 'INSERT INTO taxi.taxi_trips FORMAT CSVWithNames'
      fi
   done
   chmod +x insert_data
   ./insert_data
   ```
10. 
