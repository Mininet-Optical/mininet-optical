#!/bin/bash

set -e  # exit on error
set -u  # exit on undefined var

# Generate fake SSL certificates for netconf server/client

ipaddr=127.0.0.1   # Agent listening address
certdir=testcerts  # We create and destroy this dir to store test certs
target=localhost   # hostname use in certs and passed to -target
subj=/CN=$target   # Minimal specification for a cert

echo "* Creating cert dir $certdir"

mkdir -p $certdir

echo '* Generating fake CA cert'

openssl req -x509 -sha256 -nodes -days 2 -newkey rsa:2048 \
        -keyout $certdir/fakeca.key -out $certdir/fakeca.crt \
        -subj $subj

echo '* Generating and signing fake server cert'

openssl genrsa -out $certdir/fakeserver.key 2048

openssl req -new -key $certdir/fakeserver.key \
        -out $certdir/fakeserver.csr -subj $subj

openssl x509 -req -days 2 -in $certdir/fakeserver.csr \
        -CA $certdir/fakeca.crt -CAkey $certdir/fakeca.key \
        -set_serial 01 -out $certdir/fakeserver.crt

echo '* Generating fake client cert (self-signed)'

openssl req -x509 -sha256 -nodes -days 2 -newkey rsa:2048 \
       -keyout $certdir/fakeclient.key -out $certdir/fakeclient.crt \
       -subj $subj

echo "* Done."
exit 0
