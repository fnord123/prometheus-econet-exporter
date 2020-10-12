container:
	docker build . -t dputzolu/econet-exporter:latest

push: container
	docker push dputzolu/econet-exporter:latest
