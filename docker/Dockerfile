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
 && pip install -e . \
 && pytest --junit-xml=/tmp/pytest_unit.xml || : \
 && pytest --cov giant_time_series --cov-report=html:/tmp/coverage.html || : \
 && flake8 --exclude=env --exit-zero --statistics \
    --output-file=/tmp/flake8.log --tee \
 && pylint --ignore env --exit-zero --output-format \
    parseable giant_time_series tests > /tmp/pylint.log || : \
 && rm -rf /home/ops/.cache

WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
