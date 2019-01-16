FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# Update
#RUN apt-get update

# Here we install a python coverage tool and an
# https library that is out of date in the base image.
RUN pip install coverage &&\
    apt-get update && apt-get install build-essential zlib1g-dev

# For minimap2 bin
WORKDIR /kb/module
RUN \
    git clone https://github.com/lh3/minimap2 && \
    cd minimap2 && make && \
    export PATH=/kb/module/minimap2:$PATH

# For Krona Tools
RUN \
    git clone https://github.com/marbl/Krona && \
    cd Krona/KronaTools && \
    ./install.pl && \
    export PATH=/usr/local/bin:$PATH
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
