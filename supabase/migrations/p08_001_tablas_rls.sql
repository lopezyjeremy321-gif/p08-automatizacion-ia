-- P08: tablas con prefijo p08_ en el esquema public. Idempotente. RLS obligatorio.
-- Cada fila pertenece a un usuario autenticado (owner_id). Sin politicas para el rol anon: la clave
-- publishable sola NO puede leer ni escribir nada; hace falta un JWT de usuario.

create table if not exists public.p08_tasks (
  id text primary key,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  message_id text not null check (length(message_id) <= 200),
  from_email text not null check (from_email !~ '[\r\n]' and length(from_email) <= 254),
  from_name text not null default '' check (from_name !~ '[\r\n]'),
  subject text not null check (subject !~ '[\r\n]' and length(subject) <= 200),
  body text not null check (length(body) <= 20000),
  label text not null check (label in ('ventas','soporte','spam','incierto')),
  confidence real not null check (confidence between 0 and 1),
  provider text not null,
  title text not null,
  priority text not null check (priority in ('alta','media','baja')),
  due_date date,
  status text not null,
  flags text not null default '',
  draft_subject text,
  draft_body text check (draft_body is null or length(draft_body) <= 2000),
  draft_version integer not null default 0,
  created_at timestamptz not null default now(),
  unique (owner_id, message_id)            -- dedupe por Message-ID
);

create table if not exists public.p08_approvals (
  id text primary key,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  task_id text not null references public.p08_tasks(id) on delete cascade,
  draft_hash text not null check (draft_hash ~ '^[0-9a-f]{64}$'),   -- sha256(tarea+destinatario+asunto+cuerpo+expiracion)
  recipient text not null check (recipient !~ '[\r\n]'),
  expires_at timestamptz not null,
  status text not null check (status in ('pending','used','rejected','superseded','expired','invalidated','send_failed')),
  decided_by text,
  created_at timestamptz not null default now()
);

create table if not exists public.p08_outbox (
  id bigint generated always as identity primary key,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  approval_id text not null unique references public.p08_approvals(id),  -- un clic = un envio
  recipient text not null check (recipient !~ '[\r\n]'),
  subject text not null check (subject !~ '[\r\n]'),
  body text not null,
  mode text not null default 'simulated' check (mode = 'simulated'),
  sent_at timestamptz not null default now()
);

create index if not exists p08_tasks_owner_idx on public.p08_tasks(owner_id, created_at desc);
create index if not exists p08_approvals_task_idx on public.p08_approvals(task_id, status);

alter table public.p08_tasks enable row level security;
alter table public.p08_approvals enable row level security;
alter table public.p08_outbox enable row level security;
alter table public.p08_tasks force row level security;
alter table public.p08_approvals force row level security;
alter table public.p08_outbox force row level security;

do $$
declare t text;
begin
  foreach t in array array['p08_tasks','p08_approvals','p08_outbox'] loop
    execute format('drop policy if exists %I on public.%I', t || '_select_own', t);
    execute format('create policy %I on public.%I for select to authenticated using (owner_id = (select auth.uid()))', t || '_select_own', t);
    execute format('drop policy if exists %I on public.%I', t || '_insert_own', t);
    execute format('create policy %I on public.%I for insert to authenticated with check (owner_id = (select auth.uid()))', t || '_insert_own', t);
  end loop;
  -- tareas y aprobaciones se actualizan (estado, borrador); el outbox es solo-insertar (sin update ni delete)
  for t in select unnest(array['p08_tasks','p08_approvals']) loop
    execute format('drop policy if exists %I on public.%I', t || '_update_own', t);
    execute format('create policy %I on public.%I for update to authenticated using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()))', t || '_update_own', t);
  end loop;
  execute 'drop policy if exists p08_tasks_delete_own on public.p08_tasks';
  execute 'create policy p08_tasks_delete_own on public.p08_tasks for delete to authenticated using (owner_id = (select auth.uid()))';
end $$;

revoke all on public.p08_tasks, public.p08_approvals, public.p08_outbox from anon;
grant select, insert, update, delete on public.p08_tasks to authenticated;
grant select, insert, update on public.p08_approvals to authenticated;
grant select, insert on public.p08_outbox to authenticated;
