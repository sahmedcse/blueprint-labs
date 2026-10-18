// Package config loads the service configuration from environment variables.
package config

import (
	"errors"
	"fmt"
	"log/slog"
	"strings"
	"time"
)

// Config is the typed configuration read once at startup.
type Config struct {
	DatabaseURL     string
	HTTPAddr        string
	LogLevel        slog.Level
	ShutdownTimeout time.Duration
}

// Load builds a Config from a lookup function such as os.LookupEnv.
// It fails fast when a required variable is missing or a value does not parse.
func Load(lookup func(string) (string, bool)) (Config, error) {
	cfg := Config{
		HTTPAddr:        ":8080",
		LogLevel:        slog.LevelInfo,
		ShutdownTimeout: 10 * time.Second,
	}

	dsn, ok := lookup("DATABASE_URL")
	if !ok || strings.TrimSpace(dsn) == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}
	cfg.DatabaseURL = dsn

	if v, ok := lookup("HTTP_ADDR"); ok && v != "" {
		cfg.HTTPAddr = v
	}
	if v, ok := lookup("LOG_LEVEL"); ok && v != "" {
		if err := cfg.LogLevel.UnmarshalText([]byte(v)); err != nil {
			return Config{}, fmt.Errorf("parse LOG_LEVEL %q: %w", v, err)
		}
	}
	if v, ok := lookup("SHUTDOWN_TIMEOUT"); ok && v != "" {
		d, err := time.ParseDuration(v)
		if err != nil {
			return Config{}, fmt.Errorf("parse SHUTDOWN_TIMEOUT %q: %w", v, err)
		}
		cfg.ShutdownTimeout = d
	}
	return cfg, nil
}
