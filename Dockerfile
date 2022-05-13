# Mondoo Multi-Architecture Container Dockerfile
# 
# To build with BuildX:   docker buildx build --build-arg VERSION=5.21.0 --platform 
#             linux/386,linux/amd64,linux/arm/v7,linux/arm64 -t mondoolabs/mondoo:5.21.0 . --push

FROM alpine:3.15
ARG VERSION

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

ARG BASEURL="https://releases.mondoo.com/mondoo/${VERSION}"
ARG PACKAGE="mondoo_${VERSION}_${TARGETOS}_${TARGETARCH}${TARGETVARIANT}.tar.gz"

RUN apk update &&\
    apk add ca-certificates wget tar rpm &&\
    wget --quiet --output-document=SHA256SUMS ${BASEURL}/checksums.linux.txt &&\
    wget --quiet --output-document=${PACKAGE} ${BASEURL}/${PACKAGE} &&\
    cat SHA256SUMS | grep "${PACKAGE}" | sha256sum -c - &&\
    tar -xzC /usr/local/bin -f ${PACKAGE} &&\
    /usr/local/bin/mondoo version &&\
    rm -f ${PACKAGE} SHA256SUMS &&\
    apk del wget tar --quiet &&\
    rm -rf /var/cache/apk/*

# Note: we would prefer to use our own user to ensure the image does not run in root, but this comes with a lot of
# limitations:
# - difficulties with docker volume mounting
# - will not work properly in gcp cloud run (especially with data mounting)
# TODO: revist in future if limitations are still true
# RUN addgroup -S mondoo && adduser -S -G mondoo mondoo
# USER mondoo
ENTRYPOINT [ "mondoo" ]
CMD ["help"]
