# Установка
1. Устанавливаем Docker согласно официальной инструкции: https://docs.docker.com/engine/install/ubuntu/
2. Запускаем:
   ```sh
   docker run \
   --name otus-redis-7.2 \
   -v "$(pwd)/redis.conf":/etc/redis/redis.conf \
   -p 6379:6379 \
   -d \
   redis:7.2.5 redis-server /etc/redis/redis.conf
   ```
   ```sh
   docker start otus-redis-7.2
   ```
3. Устанавливаем python3-redis:
   ```sh
   sudo apt install python3-redis
   ```
# Загрузка JSON
5. Скачиваем тестовый JSON: https://github.com/json-iterator/test-data/raw/refs/heads/master/large-file.json
6. Подготавливаем скрипт Python:
   ```python
   import json
   import redis

   # Подключение к Redis
   r = redis.Redis(host='localhost', port=6379, db=0)

   # Чтение JSON-файла
   with open('github_events.json', 'r', encoding='utf-8') as f:
    events = json.load(f)

   # Загрузка каждого события в Redis
   for event in events:
    # Используем ID события как ключ
    event_id = event['id']
    
    # 1. Сохраняем весь объект события как строку JSON
    r.set(f'event:{event_id}', json.dumps(event))
    
    # 2. Дополнительные индексы для быстрого поиска (опционально)
    # По типу события
    r.sadd(f'events:type:{event["type"]}', event_id)
    
    # По пользователю (actor)
    r.sadd(f'events:actor:{event["actor"]["id"]}', event_id)
    
    # По репозиторию
    repo_key = event["repo"]["name"].replace('/', ':')
    r.sadd(f'events:repo:{repo_key}', event_id)
    
    # По дате (можно использовать Redis Sorted Sets)
    r.zadd('events:by_time', {event_id: int(event['created_at'][:10].replace('-', ''))})

   print(f"Загружено {len(events)} событий в Redis")
   ```
8. Данные загружены:
   ```sh
   evgenii@otus-nosql:~/redis$ python3 ./redis-json.py
   Загружено 11351 событий в Redis
   ```
# Кластер
10. Компируем исходный redis.conf в redis-cl.conf и делаем в нём следующие изменения:
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes
12. Запускаем 6 контейнеров
    ```sh
    docker run \
     --name otus-redis-7.2-1 \
     -h redis-1 \
     -v "$(pwd)/redis-cl.conf":/etc/redis/redis.conf \
     -p 63791:6379 \
     -d \
     redis:7.2.5 redis-server /etc/redis/redis.conf
    ```
    ```sh
    docker run \
     --name otus-redis-7.2-2 \
     -h redis-2 \
     -v "$(pwd)/redis-cl.conf":/etc/redis/redis.conf \
     -p 63792:6379 \
     -d \
     redis:7.2.5 redis-server /etc/redis/redis.conf
    ```
    и т. д., меняя имя контейнера, имя хоста внутри, внешний порт 
14. Собираем кластер из первого узла (на IP - не разбирался с резолвингом redis-1...6):
    ```sh
    docker exec -it otus-redis-7.2-1 redis-cli --cluster create 172.17.0.3:6379 172.17.0.4:6379 172.17.0.5:6379 172.17.0.6:6379 172.17.0.7:6379  172.17.0.7:6379 --cluster-replicas 1
    ```
    Получаем:
    ```sh
    >>> Performing hash slots allocation on 6 nodes...
    Master[0] -> Slots 0 - 5460
    Master[1] -> Slots 5461 - 10922
    Master[2] -> Slots 10923 - 16383
    Adding replica 172.17.0.7:6379 to 172.17.0.3:6379
    Adding replica 172.17.0.7:6379 to 172.17.0.4:6379
    Adding replica 172.17.0.6:6379 to 172.17.0.5:6379
    M: 6e4a400a2ff84e5657e7a4b447f7572d1577d9ee 172.17.0.3:6379
       slots:[0-5460] (5461 slots) master
    M: 1ca12ea7522ae5c6eda3f2d63ffca4d9bec6f59a 172.17.0.4:6379
       slots:[5461-10922] (5462 slots) master
    M: f1b087d8e6e2807427a15f8ee8b40e861f801dde 172.17.0.5:6379
       slots:[10923-16383] (5461 slots) master
    S: 3537423839552fd4fced1f192f4f2d7237430a01 172.17.0.6:6379
       replicates f1b087d8e6e2807427a15f8ee8b40e861f801dde
    S: 59b08bdb6b21fd8582efbb6a1630bafe65783ed3 172.17.0.7:6379
       replicates 6e4a400a2ff84e5657e7a4b447f7572d1577d9ee
    S: 59b08bdb6b21fd8582efbb6a1630bafe65783ed3 172.17.0.7:6379
       replicates 1ca12ea7522ae5c6eda3f2d63ffca4d9bec6f59a
    Can I set the above configuration? (type 'yes' to accept): yes
    >>> Nodes configuration updated
    >>> Assign a different config epoch to each node
    >>> Sending CLUSTER MEET messages to join the cluster
    Waiting for the cluster to join
    .
    >>> Performing Cluster Check (using node 172.17.0.3:6379)
    M: 6e4a400a2ff84e5657e7a4b447f7572d1577d9ee 172.17.0.3:6379
       slots:[0-5460] (5461 slots) master
    S: 3537423839552fd4fced1f192f4f2d7237430a01 172.17.0.6:6379
       slots: (0 slots) slave
       replicates f1b087d8e6e2807427a15f8ee8b40e861f801dde
    S: 59b08bdb6b21fd8582efbb6a1630bafe65783ed3 172.17.0.7:6379
       slots: (0 slots) slave
       replicates 1ca12ea7522ae5c6eda3f2d63ffca4d9bec6f59a
    M: 1ca12ea7522ae5c6eda3f2d63ffca4d9bec6f59a 172.17.0.4:6379
       slots:[5461-10922] (5462 slots) master
       1 additional replica(s)
    M: f1b087d8e6e2807427a15f8ee8b40e861f801dde 172.17.0.5:6379
       slots:[10923-16383] (5461 slots) master
       1 additional replica(s)
    [OK] All nodes agree about slots configuration.
    >>> Check for open slots...
    >>> Check slots coverage...
    [OK] All 16384 slots covered.
    ```
16. Проверяем статус:
    ```sh
    evgenii@otus-nosql:~/redis$ docker exec -it otus-redis-7.2-1 redis-cli
    127.0.0.1:6379> cluster info
    cluster_state:ok
    ```
