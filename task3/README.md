# Jaeger в Minikube с сервисами

## Описание
Развертывание Jaeger в Minikube с двумя сервисами, которые:
1. Взаимодействуют между собой
2. Отправляют трейсы в Jaeger

## Требования
- Minikube
- kubectl
- Docker

## Установка

### 1. Запуск Minikube 
```bash
cd <project_root>/task3
minikube start --addons=ingress 
```
Ingress нужен для вызовов

### 2. Установка cert-manager
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Проверка: дождаться запуска подов
kubectl get pods -n cert-manager
# NAME                                       READY   STATUS    RESTARTS   AGE
# cert-manager-7d678bfb4f-fsfzj              1/1     Running   0          23s
# cert-manager-cainjector-7449dc67b9-cqkdq   1/1     Running   0          23s
# cert-manager-webhook-7789f864b7-8xs6x      1/1     Running   0          23s
```

### 3. Развертывание Jaeger
```bash
kubectl create namespace observability

helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger-operator jaegertracing/jaeger-operator \
  --namespace observability \
  --create-namespace \
  --version 2.57.0 \
  --set rbac.clusterRole=true \
  --set rbac.clusterRoleRules[0].apiGroups="{networking.k8s.io}" \
  --set rbac.clusterRoleRules[0].resources="{ingressclasses}" \
  --set rbac.clusterRoleRules[0].verbs="{get,list,watch}"
# Проверка: дождаться запуска подов
kubectl get pods -n observability -l app.kubernetes.io/name=jaeger-operator
# NAME                               READY   STATUS    RESTARTS   AGE
# jaeger-operator-5dd4467d59-qktlz   1/1     Running   0          81s

kubectl apply -f k8s/jaeger-instance.yaml -n observability
# Проверка: дождаться запуска сервисов
kubectl get svc -n observability
# NAME                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                                                              AGE
# jaeger-operator-metrics           ClusterIP   10.106.70.10    <none>        8383/TCP                                                             2m21s
# jaeger-operator-webhook-service   ClusterIP   10.99.55.168    <none>        443/TCP                                                              2m21s
# simplest-agent                    ClusterIP   None            <none>        5775/UDP,5778/TCP,6831/UDP,6832/UDP,14271/TCP                        47s
# simplest-collector                ClusterIP   10.97.209.249   <none>        9411/TCP,14250/TCP,14267/TCP,14268/TCP,14269/TCP,4317/TCP,4318/TCP   47s
# simplest-collector-headless       ClusterIP   None            <none>        9411/TCP,14250/TCP,14267/TCP,14268/TCP,14269/TCP,4317/TCP,4318/TCP   47s
# simplest-query                    ClusterIP   10.103.234.31   <none>        16686/TCP,16685/TCP,16687/TCP                                        47s
```

### 4. Сборка и деплой сервисов
```bash
# Сборка образов
minikube image build -t shop-api:latest services/shop-api/
minikube image build -t mes-api:latest services/mes-api/

# Развертывание
kubectl apply -f k8s/services.yaml -n observability
```

## Проверка работы

### Доступ к Jaeger UI
```bash
kubectl port-forward svc/simplest-query 16686:16686 -n observability &
kubectl port-forward svc/shop-api 8000:8000 -n observability &
kubectl port-forward svc/mes-api 8001:8001 -n observability &
```

### Тестирование сервисов
Через [браузер](http://localhost:16686) и Postman [коллекцию](./services/Observability.postman_collection.json).

## Структура проекта
- `services/shop-api/` - Исходный код shop-api
- `services/mes-api/` - Исходный код mes-api 
- `k8s/services.yaml` - Конфигурация Kubernetes для сервисов
- `k8s/jaeger-instance.yaml` - Конфигурация Jaeger
