CREATE INDEX IF NOT EXISTS idx_traffic_incident_vehicle
ON SCHEMA_NAME.traffic_incident(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_traffic_incident_sensor
ON SCHEMA_NAME.traffic_incident(sensor_id);

CREATE INDEX IF NOT EXISTS idx_traffic_incident_occurred_at
ON SCHEMA_NAME.traffic_incident(occurred_at);

CREATE INDEX IF NOT EXISTS idx_fine_traffic_incident
ON SCHEMA_NAME.fine(traffic_incident_id);

CREATE INDEX IF NOT EXISTS idx_fine_pending
ON SCHEMA_NAME.fine(status)
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_fine_due_date
ON SCHEMA_NAME.fine(due_date);

CREATE INDEX IF NOT EXISTS idx_fine_payment_fine
ON SCHEMA_NAME.fine_payment(fine_id);

CREATE INDEX IF NOT EXISTS idx_fine_payment_paid_at
ON SCHEMA_NAME.fine_payment(paid_at);

CREATE INDEX IF NOT EXISTS idx_vehicle_app_user
ON SCHEMA_NAME.vehicle(app_user_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_allowed_true
ON SCHEMA_NAME.vehicle(app_user_id)
WHERE allowed = TRUE;

CREATE INDEX IF NOT EXISTS idx_sensor_app_user_active
ON SCHEMA_NAME.sensor(app_user_id)
WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS idx_app_user_notification_app_user
ON SCHEMA_NAME.app_user_notification(app_user_id);

CREATE INDEX IF NOT EXISTS idx_app_user_notification_unread
ON SCHEMA_NAME.app_user_notification(app_user_id)
WHERE read_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_audit_log_app_user
ON SCHEMA_NAME.audit_log(app_user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at
ON SCHEMA_NAME.audit_log(changed_at);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_operation
ON SCHEMA_NAME.audit_log(table_name, operation);

CREATE INDEX IF NOT EXISTS idx_audit_log_row_id
ON SCHEMA_NAME.audit_log(row_id);

CREATE INDEX IF NOT EXISTS idx_fine_citizen
ON SCHEMA_NAME.fine(citizen_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_row
ON SCHEMA_NAME.audit_log(table_name, row_id);

CREATE UNIQUE INDEX uniq_app_user_username_active
ON SCHEMA_NAME.app_user (username)
WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_citizen_cpf_active
ON SCHEMA_NAME.citizen (cpf)
WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_citizen_email_active
ON SCHEMA_NAME.citizen (email)
WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_vehicle_license_plate_active
ON SCHEMA_NAME.vehicle (license_plate)
WHERE deleted_at IS NULL;