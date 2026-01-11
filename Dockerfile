FROM ubuntu:22.04

ENV TZ=Europe/Rome
RUN apt -y update
RUN apt -y upgrade

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

RUN apt install -y net-tools \
iproute2 \
iputils-ping \
vim \
netcat \
sudo

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gcc g++ \
    pkg-config make cmake ninja-build \
    protobuf-compiler protobuf-c-compiler \
    autoconf automake libtool \
    texinfo git mercurial curl \
    flex bison xmlto \
    python3-venv \
    clang-format clangd \
    doxygen dia graphviz \
    libcomedi-dev \
    libconfig-dev \
    libcurl4-openssl-dev \
    libfmt-dev \
    libibverbs-dev \
    libjansson-dev \
    liblua5.3-dev \
    libmodbus-dev \
    libmosquitto-dev \
    libnanomsg-dev \
    libnl-3-dev libnl-route-3-dev \
    libprotobuf-c-dev \
    libprotobuf-dev \
    librabbitmq-dev \
    librdkafka-dev \
    librdmacm-dev \
    libre2-dev \
    libspdlog-dev \
    libssl-dev \
    libusb-1.0-0-dev \
    libzmq3-dev \
    uuid-dev \
    libre2-dev \
    libglib2.0-dev \
    libcriterion-dev

RUN git clone https://github.com/VILLASframework/node.git VILLASnode

WORKDIR /VILLASnode

RUN git submodule update --init common
RUN git submodule update --init --recursive

ENV PREFIX=/usr/local
RUN DEPS_NONINTERACTIVE=1 bash packaging/deps.sh
RUN cmake -S . -B ./build -DCMAKE_BUILD_TYPE=Release
RUN cmake --build ./build --target install
RUN DEPS_INCLUDE='uldaq jansson' bash packaging/deps.sh

# Create nodeuser user with sudo privileges
RUN useradd -ms /bin/bash nodeuser && \
    usermod -aG sudo nodeuser
# New added for disable sudo password
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN chown -R nodeuser /VILLASnode /tmp

USER nodeuser

ENTRYPOINT [ "sudo", "-i"]

CMD ["/bin/bash"]