FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY src ./src
COPY roles.json ./roles.json

EXPOSE 4000

CMD ["node", "src/index.js"]
