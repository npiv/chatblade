FROM python:3.11-slim

RUN adduser chatblader
RUN mkdir -p /opt/chatblade

COPY . /opt/chatblade
RUN chown -R chatblader:chatblader /opt/chatblade
USER chatblader
WORKDIR /opt/chatblade

RUN pip install --upgrade pip
RUN pip install .

ENV PATH="$PATH:/home/chatblader/.local/bin"

ENTRYPOINT ["chatblade"]
