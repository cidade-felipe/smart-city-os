-- Essa função aplica multa ao wallet do cidadão quando um incidente de trânsito é criado
-- Esta função é acionada após a inserção de um incidente de trânsito
-- Deduz o valor da multa do saldo da carteira do cidadão
-- Se o saldo for insuficiente, transfere o valor para dívida e bloqueia o acesso

CREATE OR REPLACE FUNCTION apply_fine_to_wallet()
RETURNS TRIGGER AS $$
DECLARE
    v_citizen_id INTEGER;
    v_balance NUMERIC(10,2);
BEGIN
    SELECT c.id, c.wallet_balance
    INTO v_citizen_id, v_balance
    FROM citizen c
    JOIN vehicle v ON v.citizen_id = c.id
    WHERE v.id = NEW.vehicle_id
    FOR UPDATE;

    IF NEW.fine_amount IS NULL OR NEW.fine_amount = 0 THEN
        RETURN NEW;
    END IF;

    IF v_balance >= NEW.fine_amount THEN
        UPDATE citizen
        SET wallet_balance = wallet_balance - NEW.fine_amount,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_citizen_id;
    ELSE
        UPDATE citizen
        SET wallet_balance = 0,
            debt = debt + (NEW.fine_amount - v_balance),
            allowed = FALSE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_citizen_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Essa função aplica pagamento de multa à dívida do cidadão quando um pagamento é feito
-- Esta função é acionada após a inserção de um pagamento de multa
-- Reduz a dívida do cidadão pelo valor pago e reativa o acesso ao veículo se a dívida for paga
CREATE OR REPLACE FUNCTION apply_fine_payment()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE citizen c
    SET debt = GREATEST(debt - NEW.amount_paid, 0),
        allowed = CASE 
            WHEN debt - NEW.amount_paid <= 0 THEN TRUE 
            ELSE allowed 
        END,
        updated_at = CURRENT_TIMESTAMP
    FROM traffic_incident ti
    JOIN vehicle v ON v.id = ti.vehicle_id
    WHERE ti.id = NEW.traffic_incident_id
      AND c.id = v.citizen_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION audit_log_generic()
RETURNS TRIGGER AS $$
DECLARE
    v_app_user_id INT;
BEGIN
    -- tenta pegar o usuário da aplicação a partir da sessão
    v_app_user_id := current_setting('app.current_user_id', true)::INT;

    INSERT INTO audit_log (
        table_name,
        operation,
        row_id,
        old_values,
        new_values,
        app_user_id
    )
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(NEW.id, OLD.id),
        CASE
            WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD)::jsonb
            ELSE NULL
        END,
        CASE
            WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW)::jsonb
            ELSE NULL
        END,
        v_app_user_id
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

