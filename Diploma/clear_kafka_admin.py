#!/usr/bin/env python3
from confluent_kafka.admin import AdminClient, ConfigResource
import sys

KAFKA_SERVERS = ['kafka1:9092', 'kafka2:9092', 'kafka3:9092']
KAFKA_TOPIC = 'test-topic'

def recreate_kafka_topic():
    """Пересоздать Kafka топик"""
    print("Пересоздание Kafka топика...")
    
    try:
        from confluent_kafka.admin import AdminClient, NewTopic
        
        admin_client = AdminClient({
            'bootstrap.servers': ','.join(KAFKA_SERVERS)
        })
        
        # Удалить топик
        try:
            fs = admin_client.delete_topics([KAFKA_TOPIC], operation_timeout=30)
            for topic, f in fs.items():
                try:
                    f.result()  # Блокирующий вызов
                    print(f"Топик {topic} удален")
                except Exception as e:
                    print(f"Ошибка удаления топика {topic}: {e}")
        except:
            print("Топик не существовал или ошибка удаления")
        
        # Создать топик заново
        try:
            new_topic = NewTopic(
                topic=KAFKA_TOPIC,
                num_partitions=3,
                replication_factor=3
            )
            fs = admin_client.create_topics([new_topic], operation_timeout=30)
            for topic, f in fs.items():
                try:
                    f.result()  # Блокирующий вызов
                    print(f"Топик {topic} создан")
                except Exception as e:
                    print(f"Ошибка создания топика {topic}: {e}")
        except Exception as e:
            print(f"Ошибка создания топика: {e}")
            
        return True
        
    except ImportError:
        print("Модуль admin не доступен")
        return False
    except Exception as e:
        print(f"Ошибка пересоздания топика: {e}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'recreate':
        recreate_kafka_topic()
    else:
        print("Использование: python clear_kafka_admin.py recreate")

if __name__ == '__main__':
    main()

