FROM node:20-alpine

WORKDIR /app

# Instalar dependencias
COPY package.json package-lock.json ./
RUN npm install

# Copiar el resto del código y construir la app
COPY . .
RUN npm run build

# Exponer el puerto
EXPOSE 3000

# Arrancar el servidor estático
CMD ["node", "server.cjs"]
