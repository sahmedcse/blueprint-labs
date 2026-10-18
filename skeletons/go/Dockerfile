# syntax=docker/dockerfile:1

FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/__NAME__ ./cmd/__NAME__

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/__NAME__ /__NAME__
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/__NAME__"]
