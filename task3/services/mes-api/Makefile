IMG_TAG=mes-api
APP_NAME=mes_api


docker-build:
	docker build -t $(IMG_TAG):latest .

docker-rm:
	docker rm $(APP_NAME)

docker-rmi:
	docker rmi $(IMG_TAG)

docker-clear:
	docker system prune

docker-run:
	docker run \
		--name $(APP_NAME) \
		$(IMG_TAG):latest
