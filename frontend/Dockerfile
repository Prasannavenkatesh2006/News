FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# Build-time environment variables will be provided by Render dashboard settings
ENV NODE_OPTIONS="--max-old-space-size=400"
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

RUN npm run build
CMD ["npm", "run", "start"]
