

-- Aplica multa ao wallet quando um incidente de trânsito é criado
-- Esta trigger deduz o valor da multa do saldo da carteira do cidadão
CREATE TRIGGER trigger_apply_fine
AFTER INSERT ON traffic_incident
FOR EACH ROW
EXECUTE FUNCTION apply_fine_to_wallet();

-- Aplica pagamento de multa para reduzir a dívida quando um pagamento é feito
-- Esta trigger atualiza a dívida do cidadão e o status de acesso quando um pagamento é registrado
-- Garante que o acesso ao veículo seja restaurado quando a dívida for paga
-- A trigger atualiza a dívida e o status de acesso do cidadão conforme necessário
-- Garante a redução adequada da dívida e o gerenciamento do acesso ao veículo
CREATE TRIGGER trigger_apply_fine_payment
AFTER INSERT ON fine_payment
FOR EACH ROW
EXECUTE FUNCTION apply_fine_payment();

-- Registra logs de auditoria para todas as tabelas que precisam de auditoria
-- Estes gatilhos registrarão todas as alterações na tabela audit_log
-- O app_user_id deve ser definido pela aplicação antes do gatilho ser acionado
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