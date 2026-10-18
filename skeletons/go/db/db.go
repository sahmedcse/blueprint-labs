// Package db embeds the goose migrations so tests and tools can apply them.
package db

import "embed"

// Migrations holds every goose migration under db/migrations.
//
//go:embed migrations/*.sql
var Migrations embed.FS
