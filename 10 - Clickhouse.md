# 1. Устанавливаем Clickhouse
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
# 2. Устанавливаем gsutil
   ```sh
   curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
   tar -xf google-cloud-cli-linux-x86_64.tar.gz
   ./google-cloud-sdk/install.sh
   ```
# 3. Скачиваем тестовые данные
   ```sh
   mkdir ./taxi_data
   gsutil -m cp -R gs://chicago10/taxi.csv.0000000000[0-3]* ./taxi_data/
   ```
# 4. Подключаемся к серверу, предварительно удалив (для целей тестирования) файл с паролем по умолчанию
   ```sh
   sudo rm /etc/clickhouse-server/users.d/default-password.xml
   clickhouse-client
   ```
# 5. Смотрим БД
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
# 6. Создадим базу данных taxi
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
# 7. Готовим исходные данные для загрузки - убираем "UTC" из файлов .csv
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
# 8. Загружаем данные в БД
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
# 9. Проверяем загруженные данные
   ```clickhouse
   select count(*) from taxi.taxi_trips
   SELECT count(*)
   FROM taxi.taxi_trips
   Query id: 1c98de53-f2ed-4380-beb5-168dc6cdb211
      ┌──count()─┐
   1. │ 26753683 │ -- 26.75 million
      └──────────┘
   1 row in set. Elapsed: 0.007 sec.
   ```
   ```clickhouse
   SELECT name, total_rows, total_bytes FROM system.tables where name='taxi_trips' FORMAT Vertical;
   SELECT
      name,
      total_rows,
      total_bytes
   FROM system.tables
   WHERE name = 'taxi_trips'
   FORMAT Vertical
   Query id: 71135c22-d3b3-4720-8568-1e1f86d69d5f
   Row 1:
   ──────
   name:        taxi_trips
   total_rows:  26753683 -- 26.75 million
   total_bytes: 3689162741 -- 3.69 billion
   1 row in set. Elapsed: 0.003 sec.
   ```
# 10. Оценка эталонного запроса
    ```clickhouse
    select payment_type, round(sum(tips)/sum(trip_total)*100, 0) + 0 as tips_percent, count(*) as c from taxi.taxi_trips group by payment_type order by 3
    SELECT
       payment_type,
       round((sum(tips) / sum(trip_total)) * 100, 0) + 0 AS tips_percent,
       count(*) AS c
    FROM taxi.taxi_trips
    GROUP BY payment_type
    ORDER BY 3 ASC
    Query id: a430335c-ae0c-42a0-ada1-f7a5c28da115
        ┌─payment_type─┬─tips_percent─┬────────c─┐
     1. │ Prepaid      │            0 │        6 │
     2. │ Way2ride     │           12 │       27 │
     3. │ Split        │           17 │      180 │
     4. │ Dispute      │            0 │     5596 │
     5. │ Pcard        │            2 │    13575 │
     6. │ No Charge    │            0 │    26294 │
     7. │ Mobile       │           16 │    61256 │
     8. │ Prcard       │            1 │    86053 │
     9. │ Unknown      │            0 │   103869 │
    10. │ Credit Card  │           17 │  9224956 │
    11. │ Cash         │            0 │ 17231871 │
        └──────────────┴──────────────┴──────────┘
    11 rows in set. Elapsed: 4.637 sec. Processed 26.75 million rows, 841.19 MB (5.77 million rows/s., 181.40 MB/s.)
    Peak memory usage: 9.61 MiB.
    ```
