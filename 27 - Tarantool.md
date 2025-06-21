1. Устанавливаем и запускаем Tarantool
   ```sh
   docker pull tarantool/tarantool:latest
   docker run -it --name mytarantool -p 3301:3301 -d tarantool/tarantool
   ```
2. Подключаемся к серверу
   ```sh
   evgenii@otus-nosql:~/tarantool$ docker exec -it mytarantool console
   ```
   ```lua
   • Connecting to the instance...
   • Connected to /var/run/tarantool/sys_env/default/instance-001/tarantool.control
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control>
   ```
3. Создаем спейс (таблицу) для хранения данных о поисках авиабилетов
   ```lua
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> ticket_searches = box.schema.space.create('ticket_searches', {
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
   ---
   ...
   ```
4. Создаем первичный индекс
   ```lua
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> ticket_searches:create_index('primary', {
    parts = {'id'},
    if_not_exists = true
   })
   ---
   - unique: true
     parts:
     - fieldno: 1
       sort_order: asc
       type: unsigned
       exclude_null: false
       is_nullable: false
     hint: true
     id: 0
     type: TREE
     space_id: 512
     name: primary
   ...
   ```
5. Создаем вторичный индекс на поля departure_date, airline и departure_city
   ```lua
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> ticket_searches:create_index('secondary_idx', {
    parts = {'departure_date', 'airline', 'departure_city'},
    if_not_exists = true,
    unique = false
   })
   ---
   - unique: false
     parts:
     - fieldno: 3
       sort_order: asc
       type: string
       exclude_null: false
       is_nullable: false
     - fieldno: 2
       sort_order: asc
       type: string
       exclude_null: false
       is_nullable: false
     - fieldno: 4
       sort_order: asc
       type: string
       exclude_null: false
       is_nullable: false
     hint: true
     id: 1
     type: TREE
     space_id: 512
     name: secondary_idx
   ...
   ```
6. Вставка записей
   ```lua
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> ticket_searches:insert{1, 'Aeroflot', '01.01.2025', 'Moscow', 'Sochi', 4500}
   ticket_searches:insert{2, 'S7', '01.01.2025', 'Novosibirsk', 'Moscow', 3200}
   ticket_searches:insert{3, 'Pobeda', '02.01.2025', 'Saint Petersburg', 'Kazan', 2500}
   ticket_searches:insert{4, 'Ural Airlines', '01.01.2025', 'Ekaterinburg', 'Moscow', 2800}
   ticket_searches:insert{5, 'Aeroflot', '03.01.2025', 'Moscow', 'Krasnodar', 3500}
   ticket_searches:insert{6, 'S7', '01.01.2025', 'Moscow', 'Irkutsk', 4200}
   ticket_searches:insert{7, 'Pobeda', '01.01.2025', 'Moscow', 'Sochi', 2900}
   ---
   ...
   ```
7. Запрос для выборки минимальной стоимости на 01.01.2025
   ```lua
   -- Создаём индекс для двух полей departure_date, min_price
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> ticket_searches:create_index('date_price_idx', {
    parts = {'departure_date', 'min_price'},
    if_not_exists = true,
    unique = false
   })
   ---
   - unique: false
     parts:
     - fieldno: 3
       sort_order: asc
       type: string
       exclude_null: false
       is_nullable: false
     - fieldno: 6
       sort_order: asc
       type: unsigned
       exclude_null: false
       is_nullable: false
     hint: true
     id: 2
     type: TREE
     space_id: 512
     name: date_price_idx
   ...
   
   -- Выбираем первое значение за 01.01.2025
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> box.space.ticket_searches.index.date_price_idx:select({'01.01.2025'}, {limit = 1})
   ---
   - - [4, 'Ural Airlines', '01.01.2025', 'Ekaterinburg', 'Moscow', 2800]
   ...
   ```
   Получили минимальную цену за 01.01.2025
   ![image](https://github.com/user-attachments/assets/f941260c-3d4e-4ce2-881d-d8d8e617da1f)
8. Функция для вывода рейсов с ценой менее 3000 рублей
   ```lua
   function find_cheap_flights(max_price)
    local cheap_flights = {}
    for _, tuple in ticket_searches:pairs() do
        if tuple.min_price < max_price then
            table.insert(cheap_flights, {
                airline = tuple.airline,
                departure_date = tuple.departure_date,
                from = tuple.departure_city,
                to = tuple.arrival_city,
                price = tuple.min_price
            })
        end
    end
    return cheap_flights
   end
   
   -- Запускаем
   /var/run/tarantool/sys_env/default/instance-001/tarantool.control> find_cheap_flights(3000)
   ---
   - - departure_date: 02.01.2025
    price: 2500
    to: Kazan
    from: Saint Petersburg
    airline: Pobeda
  - departure_date: 01.01.2025
    price: 2800
    to: Moscow
    from: Ekaterinburg
    airline: Ural Airlines
  - departure_date: 01.01.2025
    price: 2900
    to: Sochi
    from: Moscow
    airline: Pobeda
   ...
   ```
   Получили список рейсов с минимальной стоимостью билета менее 3000 рублей
   ![image](https://github.com/user-attachments/assets/28eb75eb-336b-4d75-bad6-feefd47a1a65)
