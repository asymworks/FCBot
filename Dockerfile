FROM debian:testing-slim
RUN apt-get update \
	&& apt-get -y upgrade \
	&& apt-get -y --no-install-recommends install freecad python3 python3-pip xvfb \
	&& pip3 install --break-system-packages uv

ARG FREECAD_PYTHON_VERSION=3.13

COPY . /app/
RUN chmod +x /app/entrypoint.sh

RUN cd /app \
	&& echo "${FREECAD_PYTHON_VERSION}" > .python-version \
	&& uv venv --python ${FREECAD_PYTHON_VERSION} \
	&& uv sync

WORKDIR /workspace
ENTRYPOINT [ "/app/entrypoint.sh" ]
