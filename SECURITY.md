# SECURITY.md

## Cifrado de datos (A04:2025)

### En tránsito
- MongoDB Atlas: TLS 1.2+ por defecto. La URI debe incluir `ssl=true` o ser `+srv`
  (validado en `db.py::_validar_uri`).
- No hay tráfico web (app de escritorio).

### En reposo
- MongoDB Atlas cifra en reposo con AES-256 a nivel de volumen (gestionado por Atlas).
- Contraseñas de usuarios almacenadas con bcrypt (`$2b$12$`, 60 chars, salt único).
- `.env` no versionado (`.gitignore`).
- `.env.bak` tampoco se versiona.

### Gestión de claves
- Contraseñas de usuarios: bcrypt con coste 12.
- Rotación recomendada: cada 90 días para `MONGODB_URI`.
- Rotación automática: pendiente.

### Datos sensibles en logs
- El logger `auditoria` no registra contraseñas, hashes ni URIs.
- Test `tests/test_security_review.py::TestExposicionDeSecretos` lo verifica.

## Threat Model (A06:2025)

### Actores
- **Admin**: control total.
- **Vendedor**: ventas y clientes (crear/leer), inventario solo lectura.
- **Auditor**: solo lectura en todos los módulos.
- **Atacante externo**: sin acceso al panel.

### Activos
1. Inventario (productos y stock).
2. Ventas (transacciones, folios, notas de crédito).
3. Clientes (PII: RUT, email, teléfono).
4. Usuarios (credenciales).
5. Auditoría (trazabilidad).

### Superficies de ataque
1. Login (fuerza bruta, credential stuffing).
2. Formularios (inyección NoSQL).
3. Red (MongoDB Atlas).
4. Cadena de suministro (dependencias Python).

### Controles aplicados
- RBAC con `verificar_permiso()` (A01).
- Bcrypt + bloqueo persistente tras 5 intentos (A07).
- Fortaleza de contraseña mínima (A07).
- Auditoría con retención configurable (A09).
- SBOM + pip-audit + bandit + ruff + hashes (A03, A08).
- Manejo centralizado de excepciones (A10).
- Logging a archivo (A02).

### Riesgos residuales
- Sin MFA (A07).
- Sin rate limiting por IP (app de escritorio).
- Sin cifrado de campos sensibles en MongoDB (depende de Atlas).
- Sin alertas automáticas (A09) — pendiente script `alertas.py`.

## Alertas (A09:2025)

- Script: `scripts/alertas.py`
- Recomendado ejecutar cada hora con cron o systemd timer:
cd ~/Escritorio/proyecto_boutique
cat > SECURITY.md <<'EOF'
# SECURITY.md

## Cifrado de datos (A04:2025)

### En tránsito
- MongoDB Atlas: TLS 1.2+ por defecto. La URI debe incluir `ssl=true` o ser `+srv`
  (validado en `db.py::_validar_uri`).
- No hay tráfico web (app de escritorio).

### En reposo
- MongoDB Atlas cifra en reposo con AES-256 a nivel de volumen (gestionado por Atlas).
- Contraseñas de usuarios almacenadas con bcrypt (`$2b$12$`, 60 chars, salt único).
- `.env` no versionado (`.gitignore`).
- `.env.bak` tampoco se versiona.

### Gestión de claves
- Contraseñas de usuarios: bcrypt con coste 12.
- Rotación recomendada: cada 90 días para `MONGODB_URI`.
- Rotación automática: pendiente.

### Datos sensibles en logs
- El logger `auditoria` no registra contraseñas, hashes ni URIs.
- Test `tests/test_security_review.py::TestExposicionDeSecretos` lo verifica.

## Threat Model (A06:2025)

### Actores
- **Admin**: control total.
- **Vendedor**: ventas y clientes (crear/leer), inventario solo lectura.
- **Auditor**: solo lectura en todos los módulos.
- **Atacante externo**: sin acceso al panel.

### Activos
1. Inventario (productos y stock).
2. Ventas (transacciones, folios, notas de crédito).
3. Clientes (PII: RUT, email, teléfono).
4. Usuarios (credenciales).
5. Auditoría (trazabilidad).

### Superficies de ataque
1. Login (fuerza bruta, credential stuffing).
2. Formularios (inyección NoSQL).
3. Red (MongoDB Atlas).
4. Cadena de suministro (dependencias Python).

### Controles aplicados
- RBAC con `verificar_permiso()` (A01).
- Bcrypt + bloqueo persistente tras 5 intentos (A07).
- Fortaleza de contraseña mínima (A07).
- Auditoría con retención configurable (A09).
- SBOM + pip-audit + bandit + ruff + hashes (A03, A08).
- Manejo centralizado de excepciones (A10).
- Logging a archivo (A02).

### Riesgos residuales
- Sin MFA (A07).
- Sin rate limiting por IP (app de escritorio).
- Sin cifrado de campos sensibles en MongoDB (depende de Atlas).
- Sin alertas automáticas (A09) — pendiente script `alertas.py`.

## Alertas (A09:2025)

- Script: `scripts/alertas.py`
- Recomendado ejecutar cada hora con cron o systemd timer:
