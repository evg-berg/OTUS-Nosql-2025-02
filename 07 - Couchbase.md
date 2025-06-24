# 1. Запускаем 3 сервера Couchbase
   По официальной документации https://docs.couchbase.com/server/current/install/getting-started-docker.html#multi-node-cluster-one-host
   ```sh
   docker run -d --name db1 couchbase
   docker run -d --name db2 couchbase
   docker run -d --name db3 -p 8091-8096:8091-8096 -p 11210-11211:11210-11211 couchbase
   ```
# 2. Инициализируем кластер
   Настраиваем первый сервер
   
   ![image](https://github.com/user-attachments/assets/84942bd6-51dc-41fb-a9b8-33379fcc3e41)

   Добавляем два других сервера
   
   ![image](https://github.com/user-attachments/assets/441ef62e-5466-40ad-aa4e-c71a74b664fa)

# 3. Создание БД и наполнение тестовыми данными
   ## Создание Bucket
      Имя: test_bucket
      Тип: Couchbase
      Количество памяти: 100 MB
      Replica Count: 1

   ![image](https://github.com/user-attachments/assets/cdfc007e-dc24-4f49-853d-d31f479fd129)
   ![image](https://github.com/user-attachments/assets/ef16550f-dcdf-4a38-8d33-b1a3c3d3c1ec)

   ## Наполнение тестовыми данными
   ```sql
   -- Создание первичного индекса
   CREATE PRIMARY INDEX ON `test_bucket`;

   -- Вставка тестовых данных
   INSERT INTO `test_bucket` (KEY, VALUE) 
   VALUES ("user1", {"id": "user1", "name": "John Doe", "email": "john@example.com", "type": "user"});

   INSERT INTO `test_bucket` (KEY, VALUE) 
   VALUES ("user2", {"id": "user2", "name": "Jane Smith", "email": "jane@example.com", "type": "user"});

   INSERT INTO `test_bucket` (KEY, VALUE) 
   VALUES ("order1", {"id": "order1", "user_id": "user1", "amount": 100.50, "items": ["item1", "item2"], "type": "order"});
   ```
   ## Проверка
   ```sql
   SELECT * FROM `test_bucket` WHERE type = "user";
   ```
   ![image](https://github.com/user-attachments/assets/46d9265b-35b9-41d8-a5a0-e8ae9e1cd9f6)

# 4. Проверка отказоустойчивости
   Остановка одного сервера
   ```sh
   docker stop db2
   ```
   В управлении серверами делаем failover отказавшего сервера

   ![image](https://github.com/user-attachments/assets/e6a80733-d9c9-41a3-8bc2-10ad44758c07)

   Запросы продолжают выполняться
   
   ![image](https://github.com/user-attachments/assets/e1f4f206-5c39-42cb-94bc-f3f4d7753d5e)

   Возвращаем сервер в работу
   ```sh
   docker start db2
   ```
   ![image](https://github.com/user-attachments/assets/636edbb4-0408-404b-afc8-0616248f5c0a)
