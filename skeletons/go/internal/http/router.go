// Package http holds the HTTP router, handlers and middleware.
package http

import (
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// Deps are the collaborators the handlers need. Pass them in; never use globals.
type Deps struct {
	Logger *slog.Logger
	DB     Pinger
}

// NewRouter wires middleware and routes.
func NewRouter(d Deps) http.Handler {
	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(30 * time.Second))

	r.Get("/healthz", healthHandler(d.Logger, d.DB))
	return r
}
