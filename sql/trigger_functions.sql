CREATE OR REPLACE FUNCTION apply_fine_to_wallet()
RETURNS TRIGGER AS $$
DECLARE
    v_balance NUMERIC(10,2);
BEGIN
    -- Multa cancelada ou valor zero não faz nada
    IF NEW.status = 'cancelled' OR NEW.amount IS NULL OR NEW.amount = 0 THEN
        RETURN NEW;
    END IF;

    SELECT wallet_balance
    INTO v_balance
    FROM citizen
    WHERE id = NEW.citizen_id
    FOR UPDATE;

    IF v_balance >= NEW.amount THEN
        UPDATE citizen
        SET wallet_balance = wallet_balance - NEW.amount,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.citizen_id;
    ELSE
        UPDATE citizen
        SET wallet_balance = 0,
            debt = debt + (NEW.amount - v_balance),
            allowed = FALSE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.citizen_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION apply_fine_payment()
RETURNS TRIGGER AS $$
DECLARE
    v_debt NUMERIC(10,2);
BEGIN
    SELECT debt
    INTO v_debt
    FROM citizen
    WHERE id = (
        SELECT citizen_id FROM fine WHERE id = NEW.fine_id
    )
    FOR UPDATE;

    -- Atualiza dívida do cidadão
    UPDATE citizen
    SET debt = GREATEST(debt - NEW.amount_paid, 0),
        allowed = CASE
            WHEN debt - NEW.amount_paid <= 0 THEN TRUE
            ELSE allowed
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = (
        SELECT citizen_id FROM fine WHERE id = NEW.fine_id
    );

    -- Se o método for carteira digital, também desconta saldo
    IF NEW.payment_method = 'Carteira Digital' THEN
        UPDATE citizen
        SET wallet_balance = GREATEST(wallet_balance - NEW.amount_paid, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = (
            SELECT citizen_id FROM fine WHERE id = NEW.fine_id
        );
    END IF;

    -- Marca multa como paga se quitada
    UPDATE fine
    SET status = 'paid',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.fine_id
      AND status <> 'paid'
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

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cancel_fines_when_citizen_deleted()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE fine f
    SET status = 'cancelled',
        updated_at = CURRENT_TIMESTAMP
    FROM traffic_incident ti
    JOIN vehicle v ON v.id = ti.vehicle_id
    WHERE f.traffic_incident_id = ti.id
      AND v.citizen_id = OLD.id
      AND f.status = 'pending';

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION prevent_delete_citizen_with_pending_fines()
RETURNS TRIGGER AS $$
DECLARE
    v_pending_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_pending_count
    FROM fine
    WHERE citizen_id = OLD.id
      AND status = 'pending';

    IF v_pending_count > 0 THEN
        RAISE EXCEPTION
            'Não é possível excluir o cidadão %. Existem multas pendentes.',
            OLD.id;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
