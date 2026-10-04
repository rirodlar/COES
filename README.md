# COES DSpace

Repositorio institucional de COES (Centro de Estudios de Conflicto y Cohesión
Social) sobre DSpace 9.4, desplegado con Docker en un VPS dedicado.

## Estructura

- `infra/` — docker-compose, configuración de Nginx y de DSpace (backend +
  frontend). Los valores reales (contraseñas, IP/dominio) se completan en un
  `.env` local que **no** se sube al repo (ver `infra/.env.example`).
- `theme/` — tema "custom" de DSpace Angular (extiende el tema base `dspace`):
  logo, colores, tipografía y texto del Home con la marca de COES. Para
  modificar el branding, basta con editar los archivos acá y reconstruir solo
  el contenedor del frontend — no toca el backend ni los datos.
- `import/` — pipeline de carga de metadatos desde la planilla de trabajo de
  COES hacia DSpace (formato SAF), más el crosswalk de campos
  (`Mapeo_Campos_COES_DSpace.xlsx`) y utilidades para buscar/actualizar/borrar
  ítems por `coes_id` en cargas incrementales futuras.

## Desplegar / reconstruir

1. Clonar el código fuente de DSpace backend y `dspace-angular` (tag
   `dspace-9.4`) junto a `infra/` (no se versionan acá — son el upstream
   oficial, sin modificar salvo por lo que vive en `theme/` y `infra/dspace-config/`).
2. Copiar `theme/custom/` sobre `src/themes/custom/` del checkout de
   `dspace-angular`, y descomentar el registro del tema en
   `src/themes/eager-themes.module.ts` (incluido acá como referencia).
3. Copiar `infra/dspace-config/local.cfg` a `dspace/config/local.cfg` del
   checkout del backend, y `infra/dspace-angular-config/config.yml` a
   `config/config.yml` del checkout del frontend.
4. Copiar `infra/.env.example` a `infra/.env` y completar una contraseña real.
5. `docker compose up -d --build` desde `infra/`.
6. Instalar `infra/nginx/dspace.conf` en `/etc/nginx/sites-available/` del
   host y habilitarlo.

## Carga de metadatos

```
python3 import/build_saf_coes.py "planilla.xlsx" ./saf_output --start 1 --end 388
docker cp ./saf_output dspace:/tmp/saf_output
docker exec dspace /dspace/bin/dspace import -a -e admin@correo -s /tmp/saf_output -m /tmp/mapfile.txt
```

Para cargas incrementales futuras (actualizar/evitar duplicados), usar
`find_items_by_coes_id.py` para ubicar ítems ya cargados por su `coes_id`
antes de decidir crear vs. actualizar.

Los scripts en `import/` leen credenciales desde variables de entorno
(`DSPACE_REST_URL`, `DSPACE_ADMIN_EMAIL`, `DSPACE_ADMIN_PASSWORD`), nunca
hardcodeadas.
