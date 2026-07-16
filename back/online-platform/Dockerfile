FROM node:20-alpine AS client-build

WORKDIR /app/client
COPY client/package.json ./
RUN npm install
COPY client ./
RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY src ./src
COPY --from=client-build /app/public ./public

EXPOSE 3000

CMD ["node", "src/server.js"]
