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

   
