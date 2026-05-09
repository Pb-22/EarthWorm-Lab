FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

ARG EW_URL="https://raw.githubusercontent.com/fmelon/EarthWorm-Termite-binary-files/master/EarthWorm/products/ew_for_linux"

WORKDIR /opt/ew-lab

COPY apt-packages.txt /tmp/apt-packages.txt
COPY requirements.txt /tmp/requirements.txt

RUN dpkg --add-architecture i386 \
    && apt-get update \
    && xargs -a /tmp/apt-packages.txt apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

RUN curl -fsSL "${EW_URL}" -o /usr/local/bin/ew \
    && chmod 0755 /usr/local/bin/ew \
    && file /usr/local/bin/ew | tee /opt/ew-lab/ew.file \
    && sha256sum /usr/local/bin/ew | tee /opt/ew-lab/ew.sha256 \
    && strings -a -n 6 /usr/local/bin/ew | head -n 200 > /opt/ew-lab/ew.strings.head.txt

COPY app.py /opt/ew-lab/app.py
COPY docker-compose.yml /opt/ew-lab/docker-compose.yml
COPY templates/ /opt/ew-lab/templates/
COPY static/ /opt/ew-lab/static/

RUN mkdir -p /pcaps

EXPOSE 5000
