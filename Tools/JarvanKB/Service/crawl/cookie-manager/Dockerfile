FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build
RUN npm prune --omit=dev
EXPOSE 48088
ENV COOKIE_MANAGER_CONFIG=/app/config/cookie-manager.yaml
CMD ["node", "dist/index.js"]
