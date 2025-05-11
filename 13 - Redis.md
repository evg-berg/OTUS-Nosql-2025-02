# Установка
1. https://docs.docker.com/engine/install/ubuntu/
2. Запускаем
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
3. 
4. 
