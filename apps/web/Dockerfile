FROM node:24.18.0-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json
RUN npm ci

FROM dependencies AS quality
COPY apps/web apps/web
COPY packages/contracts packages/contracts
RUN npm run lint --workspaces --if-present && \
    npm run typecheck --workspaces --if-present && \
    npm run test --workspaces --if-present

FROM dependencies AS build
COPY apps/web apps/web
COPY packages/contracts packages/contracts
RUN npm run build --workspace @journal-matcher/web

FROM node:24.18.0-alpine AS runtime
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0
WORKDIR /app
RUN apk upgrade --no-cache && \
    rm -rf /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack && \
    rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /usr/local/bin/yarn /usr/local/bin/yarnpkg && \
    addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
COPY --from=build --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
