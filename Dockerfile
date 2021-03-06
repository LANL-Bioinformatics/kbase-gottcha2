FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# Update
#RUN apt-get update

# Here we install a python coverage tool and dependency for gottcha2 
RUN pip install coverage pandas && \
    apt-get update && apt-get install -y build-essential zlib1g-dev gawk wget bioperl && \
    apt-get autoremove && apt-get clean

RUN mkdir -p /kb/data
COPY ./data/index_start.txt /kb/data/
COPY ./data/index_end.txt /kb/data/

# For minimap2 bin and Krona tools
WORKDIR /kb/module
RUN \
    git clone https://github.com/lh3/minimap2 && \
    cd minimap2 && make && \
    cp minimap2 /kb/deployment/bin && \
    cd ../ && \
    git clone https://github.com/marbl/Krona && \
    cd Krona/KronaTools && \
    ./install.pl --prefix /kb/deployment
#    ./install.pl && \
#    mkdir taxonomy && \
#    ./updateTaxonomy.sh && \
#    ./updateAccessions.sh

# For gottcha2 dbs (rest of db installation to ref data mount in entrypoint.sh init script)
RUN mkdir -p /data/gottcha2

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
