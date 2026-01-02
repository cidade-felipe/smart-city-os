CREATE INDEX IF NOT EXISTS idx_traffic_incident_vehicle
ON traffic_incident(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_traffic_incident_sensor
ON traffic_incident(sensor_id);

CREATE INDEX IF NOT EXISTS idx_traffic_incident_occurred_at
ON traffic_incident(occurred_at);

CREATE INDEX IF NOT EXISTS idx_fine_traffic_incident
ON fine(traffic_incident_id);

CREATE INDEX IF NOT EXISTS idx_fine_pending
ON fine(status)
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_fine_due_date
ON fine(due_date);

CREATE INDEX IF NOT EXISTS idx_fine_payment_fine
ON fine_payment(fine_id);

CREATE INDEX IF NOT EXISTS idx_fine_payment_paid_at
ON fine_payment(paid_at);

CREATE INDEX IF NOT EXISTS idx_vehicle_app_user
ON vehicle(app_user_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_allowed_true
ON vehicle(app_user_id)
WHERE allowed = TRUE;

CREATE INDEX IF NOT EXISTS idx_citizen_app_user
ON citizen(app_user_id);

CREATE INDEX IF NOT EXISTS idx_sensor_app_user_active
ON sensor(app_user_id)
WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS idx_app_user_notification_app_user
ON app_user_notification(app_user_id);

CREATE INDEX IF NOT EXISTS idx_app_user_notification_unread
ON app_user_notification(app_user_id)
WHERE read_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_audit_log_app_user
ON audit_log(app_user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at
ON audit_log(changed_at);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_operation
ON audit_log(table_name, operation);

CREATE INDEX IF NOT EXISTS idx_audit_log_row_id
ON audit_log(row_id);