# Stage 1: Build the React application
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
# You should pass VITE_API_URL as an environment variable in Render for this to point to your backend.
RUN npm run build

# Stage 2: Serve the built app
FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

# Render provides the PORT environment variable.
CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]
