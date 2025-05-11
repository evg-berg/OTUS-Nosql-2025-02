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
3. Устанавливаем python-pip:
   ```sh
   sudo apt install python3-redis
   ```
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
8. 
