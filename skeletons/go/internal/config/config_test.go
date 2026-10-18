package config

import (
	"log/slog"
	"testing"
	"time"
)

func TestLoad(t *testing.T) {
	const dsn = "postgres://app:pw@localhost:5432/app"
	tests := []struct {
		name    string
		env     map[string]string
		want    Config
		wantErr bool
	}{
		{
			name: "defaults",
			env:  map[string]string{"DATABASE_URL": dsn},
			want: Config{DatabaseURL: dsn, HTTPAddr: ":8080", LogLevel: slog.LevelInfo, ShutdownTimeout: 10 * time.Second},
		},
		{
			name: "overrides",
			env:  map[string]string{"DATABASE_URL": dsn, "HTTP_ADDR": ":9000", "LOG_LEVEL": "debug", "SHUTDOWN_TIMEOUT": "3s"},
			want: Config{DatabaseURL: dsn, HTTPAddr: ":9000", LogLevel: slog.LevelDebug, ShutdownTimeout: 3 * time.Second},
		},
		{name: "missing DATABASE_URL", env: map[string]string{}, wantErr: true},
		{name: "blank DATABASE_URL", env: map[string]string{"DATABASE_URL": "  "}, wantErr: true},
		{name: "bad LOG_LEVEL", env: map[string]string{"DATABASE_URL": dsn, "LOG_LEVEL": "loud"}, wantErr: true},
		{name: "bad SHUTDOWN_TIMEOUT", env: map[string]string{"DATABASE_URL": dsn, "SHUTDOWN_TIMEOUT": "soon"}, wantErr: true},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			lookup := func(k string) (string, bool) { v, ok := tc.env[k]; return v, ok }

			got, err := Load(lookup)

			if tc.wantErr {
				if err == nil {
					t.Fatalf("Load() error = nil, want an error")
				}
				return
			}
			if err != nil {
				t.Fatalf("Load() error = %v", err)
			}
			if got != tc.want {
				t.Fatalf("Load() = %+v, want %+v", got, tc.want)
			}
		})
	}
}
