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
# 3.
