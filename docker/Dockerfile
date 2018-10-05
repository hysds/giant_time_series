FROM hysds/pge-isce_giant

MAINTAINER Gerald Manipon "pymonger@gmail.com"
LABEL description="GIAnT Time Series PGEs"

USER ops

# copy packages
COPY . /home/ops/verdi/ops/giant_time_series
RUN set -ex \
 && source /home/ops/verdi/bin/activate \
 && sudo chown -R ops:ops /home/ops/verdi/ops/giant_time_series

WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
