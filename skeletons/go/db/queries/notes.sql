-- name: CreateNote :one
insert into notes (body)
values ($1)
returning id, body, created_at, updated_at;

-- name: GetNote :one
select id, body, created_at, updated_at
from notes
where id = $1;

-- name: ListNotes :many
select id, body, created_at, updated_at
from notes
order by created_at desc
limit $1;

-- name: DeleteNote :exec
delete from notes
where id = $1;
