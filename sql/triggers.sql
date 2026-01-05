-- Multas
CREATE TRIGGER trg_apply_fine
AFTER INSERT ON fine
FOR EACH ROW
EXECUTE FUNCTION apply_fine_to_wallet();

CREATE TRIGGER trg_apply_fine_payment
AFTER INSERT ON fine_payment
FOR EACH ROW
EXECUTE FUNCTION apply_fine_payment();

-- Auditoria
CREATE TRIGGER audit_app_user
AFTER INSERT OR UPDATE OR DELETE ON app_user
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_citizen
AFTER INSERT OR UPDATE OR DELETE ON citizen
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_vehicle
AFTER INSERT OR UPDATE OR DELETE ON vehicle
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_sensor
AFTER INSERT OR UPDATE OR DELETE ON sensor
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_fine
AFTER INSERT OR UPDATE OR DELETE ON fine
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_fine_payment
AFTER INSERT OR UPDATE OR DELETE ON fine_payment
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

-- App User
CREATE TRIGGER trg_soft_delete_app_user
BEFORE DELETE ON app_user
FOR EACH ROW
EXECUTE FUNCTION soft_delete_generic();

CREATE TRIGGER trg_block_update_deleted_app_user
BEFORE UPDATE ON app_user
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_generic();

-- Citizen
CREATE TRIGGER trg_soft_delete_citizen
BEFORE DELETE ON citizen
FOR EACH ROW
EXECUTE FUNCTION soft_delete_citizen_with_user();

CREATE TRIGGER trg_block_update_deleted_citizen
BEFORE UPDATE ON citizen
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_generic();

-- Vehicle
CREATE TRIGGER trg_soft_delete_vehicle
BEFORE DELETE ON vehicle
FOR EACH ROW
EXECUTE FUNCTION soft_delete_vehicle_with_user();

CREATE TRIGGER trg_block_update_deleted_vehicle
BEFORE UPDATE ON vehicle
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_generic();

-- Sensor
CREATE TRIGGER trg_soft_delete_sensor
BEFORE DELETE ON sensor
FOR EACH ROW
EXECUTE FUNCTION soft_delete_sensor_with_user();

CREATE TRIGGER trg_block_update_deleted_sensor
BEFORE UPDATE ON sensor
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_generic();
