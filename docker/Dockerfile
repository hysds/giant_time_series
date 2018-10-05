FROM hysds/pge-isce_giant

MAINTAINER Gerald Manipon "pymonger@gmail.com"
LABEL description="GIAnT Time Series PGEs"

USER ops

# copy packages
COPY . /home/ops/verdi/ops/giant_time_series
RUN set -ex \
 && sudo chown -R ops:ops /home/ops/verdi/ops/giant_time_series \
 && cd /home/ops/verdi/ops/giant_time_series \
 && sudo pip3 install virtualenv \
 && virtualenv --system-site-packages env \ 
 && source env/bin/activate \
 && pip install --process-dependency-links -e . \
 && pytest --junit-xml=/tmp/pytest_unit.xml || true \
 && rm -rf /home/ops/.cache

WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
