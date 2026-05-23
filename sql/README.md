# SQL scripts — Neurvex Audit

Run these on your PostgreSQL database **`nd_audit`**.

## Quick start (everything)

```bash
psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/install_all.sql
```

Creates `submissions`, `app_settings`, notification columns, and support inbox defaults.

## Run step by step

| File | Purpose |
|------|---------|
| `01_admin_notifications.sql` | Admin **bell** alerts when a new audit is submitted |
| `02_support_requests.sql` | **Support** page form emails |
| `install_all.sql` | Full schema + both features (recommended for new installs) |

```bash
psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/01_admin_notifications.sql
psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/02_support_requests.sql
```

## Default admin inbox

Both scripts default to:

`aakash.padyachi@rochvate.com`

Change this in the SQL files before running, or update later in **Neurvex → Settings**.

## App settings columns

| Column | Used for |
|--------|----------|
| `sender_name` | From name on outgoing audit result emails |
| `sender_address` | From address (Azure Communication Services verified domain) |
| `notification_email` | New audit alerts (bell icon must be ON) |
| `notifications_enabled` | `TRUE` = bell alerts active |
| `support_email` | Support form submissions |

## After running SQL

1. Restart the Azure Functions API  
2. In the app: **Settings** → confirm emails and from address  
3. Click the **bell** to enable new-audit notifications  
4. Test **Support** page with a sample message  
