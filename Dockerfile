FROM debian:stable-slim
LABEL maintainer="Matthew Krupczak <matthew@krupczak.org>"
RUN echo $(cat /etc/*release*)

RUN sed -i 's/stable\/updates/stable-security\/updates/' /etc/apt/sources.list
RUN apt-get update -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing --no-install-recommends python3-pip${APT_ARCH_SUFFIX}
RUN echo $(pip3 --version)

RUN useradd -ms /bin/bash user
USER user
WORKDIR /home/user

COPY requirements.txt .

RUN pip3 install -r requirements.txt && rm requirements.txt

COPY src/*.py ./
COPY src/Rome-30m-DEM.tif .
COPY src/cobb.tif .
COPY src/DJI_0419.JPG .

VOLUME /home/user

ENTRYPOINT [ "python3", "parseImage.py"]
