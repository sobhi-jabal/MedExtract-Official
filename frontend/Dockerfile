FROM node:18-alpine

WORKDIR /app

# Install curl for health checks with SSL workaround
RUN set -ex && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories && \
    apk add --no-cache curl libc6-compat

# Copy package files
COPY package*.json ./

# Install dependencies with SSL workaround
RUN npm config set strict-ssl false && \
    npm ci && \
    npm config set strict-ssl true

# Copy source code
COPY . .

# Environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the application with SSL workaround
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
RUN npm run build
ENV NODE_TLS_REJECT_UNAUTHORIZED=1

# Create nextjs user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Set ownership
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["npm", "start"]