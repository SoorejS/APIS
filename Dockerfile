FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application code (including backend and apis_demo.db)
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////app/apis_demo.db
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
