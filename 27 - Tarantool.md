1. Устанавливаем и запускаем Tarantool
   ```sh
   docker pull tarantool/tarantool:latest
   docker run -it --name mytarantool -p 3301:3301 -d tarantool/tarantool
   ```
2. Подключаемся к серверу
   ```sh
   evgenii@otus-nosql:~/tarantool$ docker exec -it mytarantool console
   • Connecting to the instance...
   • Connected to /var/run/tarantool/sys_env/default/instance-001/tarantool.control
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control>
   ```
3. Создаем спейс (таблицу) для хранения данных о поисках авиабилетов
   ```lua
   ticket_searches = box.schema.space.create('ticket_searches', {
    if_not_exists = true,
    format = {
        {name = 'id', type = 'unsigned'},
        {name = 'airline', type = 'string'},
        {name = 'departure_date', type = 'string'},
        {name = 'departure_city', type = 'string'},
        {name = 'arrival_city', type = 'string'},
        {name = 'min_price', type = 'unsigned'}
    }
   })
  ```
5. 
6. 
