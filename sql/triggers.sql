CREATE TRIGGER trigger_apply_fine
AFTER INSERT ON fine
FOR EACH ROW
EXECUTE FUNCTION apply_fine_to_wallet();

CREATE TRIGGER trigger_apply_fine_payment
AFTER INSERT ON fine_payment
FOR EACH ROW
EXECUTE FUNCTION apply_fine_payment();

CREATE TRIGGER audit_app_user
AFTER INSERT OR UPDATE OR DELETE ON app_user
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_citizen
AFTER INSERT OR UPDATE OR DELETE ON citizen
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_vehicle
AFTER INSERT OR UPDATE OR DELETE ON vehicle
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_traffic_incident
AFTER INSERT OR UPDATE OR DELETE ON traffic_incident
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_fine
AFTER INSERT OR UPDATE OR DELETE ON fine
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER audit_fine_payment
AFTER INSERT OR UPDATE OR DELETE ON fine_payment
FOR EACH ROW EXECUTE FUNCTION audit_log_generic();

CREATE TRIGGER trg_cancel_fines_on_citizen_delete
BEFORE DELETE ON citizen
FOR EACH ROW
EXECUTE FUNCTION cancel_fines_when_citizen_deleted();

CREATE TRIGGER trigger_prevent_delete_citizen_with_pending_fines
BEFORE DELETE ON citizen
FOR EACH ROW
EXECUTE FUNCTION prevent_delete_citizen_with_pending_fines();

CREATE TRIGGER trg_app_user_updated_at
BEFORE UPDATE ON app_user
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_citizen_soft_delete
BEFORE UPDATE ON citizen
FOR EACH ROW
EXECUTE FUNCTION citizen_soft_delete();

CREATE TRIGGER trg_sensor_soft_delete
BEFORE UPDATE ON sensor
FOR EACH ROW
EXECUTE FUNCTION sensor_soft_delete();
CREATE TRIGGER trg_vehicle_soft_delete
BEFORE UPDATE ON vehicle
FOR EACH ROW
EXECUTE FUNCTION vehicle_soft_delete();

CREATE TRIGGER trg_block_update_deleted_citizen
BEFORE UPDATE ON citizen
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_citizen();

CREATE TRIGGER trg_block_update_deleted_sensor
BEFORE UPDATE ON sensor
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_sensor();

CREATE TRIGGER trg_block_update_deleted_sensor
BEFORE UPDATE ON sensor
FOR EACH ROW
EXECUTE FUNCTION block_update_deleted_sensor();