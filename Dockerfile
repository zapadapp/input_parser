# python's base image
FROM python:3.9

RUN mkdir zapp

# adding app file into base directory
ADD audiorec.py ./zapp

# copying import requirements into base dir
COPY requirements.txt ./zapp

WORKDIR ./zapp
RUN ls
RUN mkdir tmp

# installing portaudio.h files so that 'pip install pyaudio' does not fail
RUN apt-get update
RUN apt-get install libsndfile1 libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y

# installing audio files for device
RUN apt-get install alsa-utils -y

# installing lilypond
RUN apt-get install lilypond -y

# installing all dependencies in 
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./audiorec.py"]