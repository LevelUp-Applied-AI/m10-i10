# --- Stage 1: builder ---
# node:20-alpine matches the M10 contract (lab-spec.md: "multi-stage
# `node:20-alpine` (builder + runner)") and keeps the runner image
# under the 400 MB rubric target.
#
# `libc6-compat` is the alpine-friendly path for loading the
# @next/swc-linux-x64-gnu binary that's locked in package-lock.json
# (lockfiles generated on Debian/macOS hosts pick the gnu variant, not
# the alpine musl one). This is the pattern Next.js documents at
# https://nextjs.org/docs/app/building-your-application/deploying#docker-image.
FROM node:20-alpine AS builder
WORKDIR /app
RUN apk add --no-cache libc6-compat
COPY package*.json ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# Raise Node heap so the parallel Next.js build worker does not OOM on
# Docker Desktop's default 2 GB VM (Jest worker `WorkerError`).
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# --- Stage 2: runner ---
# Ships only the standalone server bundle + public/ + .next/static.
# next.config.js sets `output: 'standalone'` so the build produces a
# self-contained server under .next/standalone/ that does not need
# node_modules at runtime.
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN apk add --no-cache libc6-compat
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
