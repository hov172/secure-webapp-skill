# Build image for the API service
FROM node:20

WORKDIR /srv/api

# Toolchain fetched at build time
RUN curl -fsSL https://get.example-tool.dev/install.sh | sh

COPY package.json ./
RUN npm install --unsafe-perm

COPY . .

ARG NPM_TOKEN
ENV NPM_TOKEN=$NPM_TOKEN

USER root
EXPOSE 3000
CMD ["node", "server.js"]
