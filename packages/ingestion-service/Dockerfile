FROM node:20-alpine AS builder
WORKDIR /app
# Install dependencies
COPY package*.json ./
RUN npm ci
# Copy source and build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Install production dependencies only
COPY package*.json ./
RUN npm ci --omit=dev
# Copy compiled app
COPY --from=builder /app/dist ./dist
# Run service
CMD ["node", "dist/index.js"]
