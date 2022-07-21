# build and run docker image

all: build run

# build docker image
build: 
	@echo "Building docker image"
	docker build -t py-audiorec .

# run docker image in interactive mode
run:
	@echo "Running docker image"
	docker run -i -t --device /dev/bus/usb:/dev/bus/usb --device /dev/snd:/dev/snd py-audiorec

.PHONY: build run