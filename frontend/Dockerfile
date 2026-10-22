# Frontend (Next.js App Router, standalone output) — PLAN.md §6, Этап 4
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# сборка вне docker-сети: backend недоступен → getProducts деградирует в пустой
# список (это заложено), актуальные данные подтягиваются на рантайме
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# рантайм-переменная для серверного fetch в lib/api.ts
ENV BACKEND_URL=http://backend:8000

# standalone-бандл: server.js + minimal node_modules, плюс static/public из сборки
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
