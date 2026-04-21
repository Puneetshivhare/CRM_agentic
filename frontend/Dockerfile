# Stage 1: Building the code
FROM node:20-slim AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serving the application
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0

# Copy necessary files from builder
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

# Start the application — bind explicitly to 0.0.0.0 so Docker port mapping works
CMD ["node_modules/.bin/next", "start", "-H", "0.0.0.0"]
