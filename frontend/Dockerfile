# Development Dockerfile for Next.js with hot reload
FROM node:20-alpine

WORKDIR /app

# Install dependencies only when needed
COPY package*.json ./

RUN npm install

# Don't copy source files - they will be mounted as volume for hot reload
# COPY . .

# Next.js collects anonymous telemetry - disable it
ENV NEXT_TELEMETRY_DISABLED=1

# Enable hot reload in Docker
ENV WATCHPACK_POLLING=true
ENV CHOKIDAR_USEPOLLING=true

EXPOSE 3000

# Run dev server with turbopack
CMD ["npm", "run", "dev"]
