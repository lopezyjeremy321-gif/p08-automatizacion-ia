# Supabase para P08 (opcional)

Proyecto compartido (proyecto-A). Tablas con prefijo `p08_` en `public`, siempre con RLS (`force row level security`).

- Migracion: `migrations/p08_001_tablas_rls.sql` (idempotente). La aplica el orquestador desde el SQL Editor; este proyecto no la ejecuta.
- Variables: `SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY` se leen en tiempo de ejecucion de `<ruta-local>` (o del entorno). Nunca se usa la secret/service_role key.
- La clave publishable corresponde al rol `anon`, que no tiene ninguna politica: sola no lee ni escribe. El adaptador necesita ademas un JWT de usuario (`P08_SUPABASE_JWT`, sesion del autor) y escribe filas con `owner_id = auth.uid()`.
- Dedupe por Message-ID: `unique(owner_id, message_id)`. Un clic = un envio: `unique(approval_id)` en `p08_outbox` y transicion `pending -> used` con filtro `status=eq.pending`.
- `p08_outbox` es solo-insertar y solo admite `mode = 'simulated'`.
- Adaptador: `p08/supabase_store.py`. Sin probar contra la nube (falta la migracion aplicada y un JWT); el nucleo y todas las pruebas usan SQLite.
