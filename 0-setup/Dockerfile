FROM r-base:4.3.1

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends python3 python3-pip

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN install2.r \
    SynthETIC \
    plyr \
    dplyr \
    locfit \
    actuar \
    tidyr \
    backports \
    boot \
    callr \
    cli \
    cpp11 \
    crayon \
    desc \
    digest \
    evaluate \
    fs \
    feather \
    glue \
    jsonlite \
    lattice \
    lifecycle \
    magrittr \
    Matrix \
    mgcv \
    nlme \
    nnet \
    pkgload \
    processx \
    ps \
    purrr \
    R6 \
    rlang \
    rprojroot \
    stringi \
    stringr \
    vctrs \
    withr

RUN apt-get update && apt-get install git -y
RUN mkdir -p /output/data

WORKDIR /app

COPY simulate.R .
RUN git clone https://github.com/JSchelldorfer/IndividualClaimsSimulator.git

CMD ["Rscript", "simulate.R"]
