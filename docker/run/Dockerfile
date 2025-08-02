# ~/agent-zero-core/docker/run/Dockerfile
FROM frdel/agent-zero-base:latest

ENV DEBIAN_FRONTEND=noninteractive

# build-time branch
ARG BRANCH
RUN if [ -z "$BRANCH" ]; then \
      echo "ERROR: BRANCH is not set!" >&2; exit 1; \
    fi
ENV BRANCH=${BRANCH}

# Install OS-level deps (with full upgrade to avoid python3-venv conflict)
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get install -y --no-install-recommends \
      dbus dbus-user-session libxtst6 fonts-unifont \
      libxcomposite1 libxdamage1 git && \
    rm -rf /var/lib/apt/lists/*

# create clean venv ourselves
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# copy our installer + stub playwright script
COPY fs/ins/ /ins/
RUN chmod +x /ins/install_A0.sh
#RUN chmod +x /ins/*.sh

# run just that one installer
RUN /ins/install_A0.sh ${BRANCH}

EXPOSE 22 80 9000-9009

CMD ["python3","run_cli.py","--mode","server"]
