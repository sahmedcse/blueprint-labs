package store_test

import (
	"context"
	"database/sql"
	"os"
	"testing"

	_ "github.com/jackc/pgx/v5/stdlib" // registers the "pgx" database/sql driver for goose
	"github.com/pressly/goose/v3"

	"github.com/__OWNER__/__NAME__/db"
	"github.com/__OWNER__/__NAME__/internal/store"
)

// TestNotesRoundTrip runs against a real, ephemeral Postgres. It is the only test
// allowed to skip, and only when DATABASE_URL is unset (see the Makefile).
func TestNotesRoundTrip(t *testing.T) {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		t.Skip("DATABASE_URL not set: skipping integration test")
	}
	ctx := t.Context()

	migrate(t, dsn)

	s, err := store.Open(ctx, dsn)
	if err != nil {
		t.Fatalf("open store: %v", err)
	}
	t.Cleanup(s.Close)

	if err := s.Ping(ctx); err != nil {
		t.Fatalf("ping: %v", err)
	}

	created, err := s.CreateNote(ctx, "buy oat milk")
	if err != nil {
		t.Fatalf("create note: %v", err)
	}
	t.Cleanup(func() {
		if err := s.DeleteNote(context.Background(), created.ID); err != nil {
			t.Errorf("delete note: %v", err)
		}
	})

	got, err := s.GetNote(ctx, created.ID)
	if err != nil {
		t.Fatalf("get note: %v", err)
	}
	if got.Body != "buy oat milk" {
		t.Fatalf("body = %q, want %q", got.Body, "buy oat milk")
	}
	if !got.CreatedAt.Valid || !got.UpdatedAt.Valid {
		t.Fatalf("timestamps not set: created_at=%v updated_at=%v", got.CreatedAt, got.UpdatedAt)
	}

	if _, err := s.CreateNote(ctx, ""); err == nil {
		t.Fatalf("create note with empty body: error = nil, want check violation")
	}
}

// migrate applies the embedded goose migrations. It is idempotent.
func migrate(t *testing.T, dsn string) {
	t.Helper()
	sqlDB, err := sql.Open("pgx", dsn)
	if err != nil {
		t.Fatalf("open sql db: %v", err)
	}
	t.Cleanup(func() {
		if err := sqlDB.Close(); err != nil {
			t.Errorf("close sql db: %v", err)
		}
	})

	goose.SetBaseFS(db.Migrations)
	if err := goose.SetDialect("postgres"); err != nil {
		t.Fatalf("set goose dialect: %v", err)
	}
	if err := goose.UpContext(t.Context(), sqlDB, "migrations"); err != nil {
		t.Fatalf("apply migrations: %v", err)
	}
}
