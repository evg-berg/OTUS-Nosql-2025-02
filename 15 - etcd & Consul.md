# etcd
1. Поднимаем 3 узла в докере:
   ```yml
   services:
    etcd1:
      image: docker.io/bitnami/etcd:latest
      container_name: etcd1
      hostname: etcd1
      restart: always
      environment:
        - ALLOW_NONE_AUTHENTICATION=yes
        - ETCD_NAME=etcd1
        - ETCD_INITIAL_ADVERTISE_PEER_URLS=http://etcd1:2380
        - ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380
        - ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379
        - ETCD_ADVERTISE_CLIENT_URLS=http://etcd1:2379
        - ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster
        - ETCD_INITIAL_CLUSTER=etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380
        - ETCD_INITIAL_CLUSTER_STATE=new
      ports:
        - 2381:2379
      volumes:
        - ./data/etcd1:/etcd_data

    etcd2:
      image: docker.io/bitnami/etcd:latest
      container_name: etcd2
      hostname: etcd2
      restart: always
      environment:
        - ALLOW_NONE_AUTHENTICATION=yes
        - ETCD_NAME=etcd2
        - ETCD_INITIAL_ADVERTISE_PEER_URLS=http://etcd2:2380
        - ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380
        - ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379
        - ETCD_ADVERTISE_CLIENT_URLS=http://etcd2:2379
        - ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster
        - ETCD_INITIAL_CLUSTER=etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380
        - ETCD_INITIAL_CLUSTER_STATE=new
      ports:
        - 2382:2379
      volumes:
        - ./data/etcd2:/etcd_data

    etcd3:
      image: docker.io/bitnami/etcd:latest
      container_name: etcd3
      hostname: etcd3
      restart: always
      environment:
        - ALLOW_NONE_AUTHENTICATION=yes
        - ETCD_NAME=etcd3
        - ETCD_INITIAL_ADVERTISE_PEER_URLS=http://etcd3:2380
        - ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380
        - ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379
        - ETCD_ADVERTISE_CLIENT_URLS=http://etcd3:2379
        - ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster
        - ETCD_INITIAL_CLUSTER=etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380
        - ETCD_INITIAL_CLUSTER_STATE=new
      ports:
        - 2383:2379
      volumes:
        - ./data/etcd3:/etcd_data
   ```
3. 
