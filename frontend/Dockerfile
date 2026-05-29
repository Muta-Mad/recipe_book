# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --prefer-offline
COPY . ./
RUN npm run build
CMD cp -r build result_build
