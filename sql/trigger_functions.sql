CREATE OR REPLACE FUNCTION apply_fine_to_wallet()
RETURNS TRIGGER AS $$
DECLARE
    v_citizen_id INTEGER;
    v_balance NUMERIC(10,2);
BEGIN
    SELECT c.id, c.wallet_balance
    INTO v_citizen_id, v_balance
    FROM traffic_incident ti
    JOIN vehicle v ON v.id = ti.vehicle_id
    JOIN citizen c ON c.id = v.citizen_id
    WHERE ti.id = NEW.traffic_incident_id
    FOR UPDATE;

    -- Se não houver cidadão associado, não faz nada
    IF v_citizen_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Se o valor da multa for zero, ignora
    IF NEW.amount IS NULL OR NEW.amount = 0 THEN
        RETURN NEW;
    END IF;

    IF v_balance >= NEW.amount THEN
        UPDATE citizen
        SET wallet_balance = wallet_balance - NEW.amount,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_citizen_id;
    ELSE
        UPDATE citizen
        SET wallet_balance = 0,
            debt = debt + (NEW.amount - v_balance),
            allowed = FALSE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_citizen_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION apply_fine_payment()
RETURNS TRIGGER AS $$
DECLARE
    v_citizen_id INTEGER;
BEGIN
    SELECT c.id
    INTO v_citizen_id
    FROM fine f
    JOIN traffic_incident ti ON ti.id = f.traffic_incident_id
    JOIN vehicle v ON v.id = ti.vehicle_id
    JOIN citizen c ON c.id = v.citizen_id
    WHERE f.id = NEW.fine_id
    FOR UPDATE;

    IF v_citizen_id IS NULL THEN
        RETURN NEW;
    END IF;

    UPDATE citizen
    SET debt = GREATEST(debt - NEW.amount_paid, 0),
        allowed = CASE
            WHEN debt - NEW.amount_paid <= 0 THEN TRUE
            ELSE allowed
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_citizen_id;

    UPDATE fine
    SET status = 'paid',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.fine_id
      AND amount <= (
          SELECT COALESCE(SUM(fp.amount_paid), 0)
          FROM fine_payment fp
          WHERE fp.fine_id = NEW.fine_id
      );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION audit_log_generic()
RETURNS TRIGGER AS $$
DECLARE
    v_app_user_id INTEGER;
BEGIN
    v_app_user_id := current_setting('app.current_user_id', true)::INTEGER;

    INSERT INTO audit_log (
        table_name,
        operation,
        row_id,
        old_values,
        new_values,
        app_user_id,
        performed_by_app_user_id
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
        v_app_user_id,
        v_app_user_id
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
