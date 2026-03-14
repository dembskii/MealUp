FROM node:20-alpine AS base

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS deps

COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

FROM base AS runner

ENV APP_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY . .
COPY --from=builder /app/.next ./.next
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh && mkdir -p /app/.next && chown -R node:node /app

USER node

EXPOSE 3000

ENTRYPOINT ["docker-entrypoint.sh"]
