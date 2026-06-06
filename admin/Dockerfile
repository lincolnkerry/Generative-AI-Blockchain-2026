FROM node:22-alpine AS builder

WORKDIR /app

# Pin pnpm to match lockfile version
RUN corepack enable && corepack prepare pnpm@10.33.0 --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
