# 1. Установка RabbitMQ
   ```sh
   docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.9-management
   ```
   ![image](https://github.com/user-attachments/assets/69e3a578-082a-4763-b8d0-d9489986327e)
# 2. Exchange и Queue
   Создаём Exchange otus_ex1 в http://51.250.84.117:15672/#/exchanges
   ![image](https://github.com/user-attachments/assets/34bc4dc1-a21d-4dd6-8a0d-87c02940fb84)
   
   Создаём Queue otus_que1 в http://51.250.84.117:15672/#/queues
   ![image](https://github.com/user-attachments/assets/01b73817-7845-40ff-83ec-7b86770361fa)
   
   И связываем их
# 3. Публикация и чтение сообщений
   ![image](https://github.com/user-attachments/assets/42727acb-c9fe-4eb3-9cac-7d6f705d3e80)

# 4. Программная отправка и чтение
   ```python
   import pika

   # Подключение к серверу RabbitMQ
   connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
   channel = connection.channel()

   # Текущее время
   from datetime import datetime
   current_time = datetime.now().strftime("%H:%M:%S")

   # Отправка сообщения
   channel.basic_publish(
       exchange='',
       routing_key='otus_que1',  # имя очереди
       body="Hello, OTUS! {}".format(current_time)
   )
   print(" [x] Sent {}".format(current_time))

   # Закрытие соединения
   connection.close()
   ```
