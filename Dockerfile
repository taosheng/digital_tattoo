# Stage 1: Build Frontend
FROM node:18 AS frontend-build
WORKDIR /app/frontend

COPY src/frontend/package*.json ./
RUN npm install

COPY src/frontend/ .
# Build arguments for frontend
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
# API URL is relative, so we don't strictly need VITE_API_URL, but keeping it empty or default is fine.
RUN npm run build

# Stage 2: Build Backend & Serve
FROM python:3.14-slim

WORKDIR /app

# Install backend dependencies
COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire src tree
COPY src/ /app/src/

# Copy config files
COPY .env* saltycat.json* /app/
# Copy Arweave wallet key file
COPY ar_new_wallet_1.json /app/

# Copy frontend build to backend static folder
COPY --from=frontend-build /app/frontend/dist /app/src/backend/static

# Expose port
ENV PORT=8080
EXPOSE 8080

# Run FastAPI with Uvicorn targeting the module
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
