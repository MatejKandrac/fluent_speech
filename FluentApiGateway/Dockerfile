# Build stage
FROM gradle:8.5-jdk21 AS build

# Set working directory
WORKDIR /app

# Copy gradle files
COPY build.gradle.kts settings.gradle.kts ./
COPY gradle ./gradle

# Copy source code
COPY src ./src

# Build the application
RUN gradle build --no-daemon -x test

# Run stage
FROM eclipse-temurin:21-jre-jammy

# Set working directory
WORKDIR /app

# Copy the built JAR from build stage
COPY --from=build /app/build/libs/*.jar app.jar

# Expose port
EXPOSE 8000

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]
