FROM osgeo/gdal:ubuntu-small-3.5.0
LABEL maintainer="Matthew Krupczak <matthew@krupczak.org>"
RUN echo $(cat /etc/*release*)
# # ----------GDAL-STUFF----------
# RUN apt-get update
# RUN apt-get upgrade -y

# RUN echo deb https://ftp.debian.org/debian unstable main contrib non-free >> /etc/apt/sources.list
# RUN apt-get update

# RUN apt-get remove -y binutils

# RUN apt-get -t unstable install -y libgdal-dev g++

# ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
# ENV C_INCLUDE_PATH=/usr/include/gdal

# # RUN pip install pygdal~=3.2.0 #included in requirenments.txt instead
# # ----------END-GDAL-STUFF----------

RUN apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing --no-install-recommends python3-pip${APT_ARCH_SUFFIX}
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

ENTRYPOINT [ "python", "parseImage.py"]
