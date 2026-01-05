CREATE OR REPLACE FUNCTION apply_fine_to_wallet()
RETURNS TRIGGER AS $$
DECLARE
    v_balance NUMERIC(10,2);
BEGIN
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
    v_citizen_id INTEGER;
BEGIN
    SELECT citizen_id
    INTO v_citizen_id
    FROM fine
    WHERE id = NEW.fine_id;

    UPDATE citizen
    SET debt = GREATEST(debt - NEW.amount_paid, 0),
        allowed = CASE
            WHEN debt - NEW.amount_paid <= 0 THEN TRUE
            ELSE allowed
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_citizen_id;

    IF NEW.payment_method = 'Carteira Digital' THEN
        UPDATE citizen
        SET wallet_balance = GREATEST(wallet_balance - NEW.amount_paid, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_citizen_id;
    END IF;

    UPDATE fine
    SET status = 'paid',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.fine_id
      AND amount <= (
          SELECT COALESCE(SUM(amount_paid), 0)
          FROM fine_payment
          WHERE fine_id = NEW.fine_id
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
        CASE WHEN TG_OP IN ('UPDATE','DELETE') THEN row_to_json(OLD)::jsonb END,
        CASE WHEN TG_OP IN ('INSERT','UPDATE') THEN row_to_json(NEW)::jsonb END,
        v_app_user_id,
        v_app_user_id
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION soft_delete_generic()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM set_config('app.soft_delete', 'true', true);

    EXECUTE format(
        'UPDATE %I SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, allowed = FALSE WHERE id = $1',
        TG_TABLE_NAME
    )
    USING OLD.id;

    PERFORM set_config('app.soft_delete', 'false', true);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION block_update_deleted_generic()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('app.soft_delete', true) = 'true' THEN
        RETURN NEW;
    END IF;

    IF OLD.deleted_at IS NOT NULL THEN
        RAISE EXCEPTION
            'Registro % da tabela % está deletado e não pode ser alterado',
            OLD.id, TG_TABLE_NAME;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION block_update_deleted_row()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL THEN
        RETURN NEW;
    END IF;

    IF OLD.deleted_at IS NOT NULL THEN
        RAISE EXCEPTION
            'Registro % da tabela % está deletado e não pode ser alterado',
            OLD.id, TG_TABLE_NAME;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION soft_delete_citizen_with_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Soft delete do app_user associado
    UPDATE app_user 
    SET deleted_at = CURRENT_TIMESTAMP, 
        updated_at = CURRENT_TIMESTAMP, 
        allowed = FALSE 
    WHERE id = OLD.app_user_id;
    
    -- Soft delete do citizen
    UPDATE citizen 
    SET deleted_at = CURRENT_TIMESTAMP, 
        updated_at = CURRENT_TIMESTAMP, 
        allowed = FALSE 
    WHERE id = OLD.id;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION soft_delete_vehicle_with_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Soft delete do app_user associado
    UPDATE app_user 
    SET deleted_at = CURRENT_TIMESTAMP, 
        updated_at = CURRENT_TIMESTAMP, 
        allowed = FALSE 
    WHERE id = OLD.app_user_id;
    
    -- Soft delete do vehicle
    UPDATE vehicle 
    SET deleted_at = CURRENT_TIMESTAMP, 
        updated_at = CURRENT_TIMESTAMP, 
        allowed = FALSE 
    WHERE id = OLD.id;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION soft_delete_sensor_with_user()
RETURNS TRIGGER AS $$
BEGIN
-- Soft delete do app_user associado
UPDATE app_user 
SET deleted_at = CURRENT_TIMESTAMP, 
    updated_at = CURRENT_TIMESTAMP, 
    allowed = FALSE 
WHERE id = OLD.app_user_id;

-- Soft delete do sensor
UPDATE sensor 
SET deleted_at = CURRENT_TIMESTAMP, 
    updated_at = CURRENT_TIMESTAMP, 
    active = FALSE 
WHERE id = OLD.id;

RETURN NULL;
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

CREATE OR REPLACE FUNCTION cancel_fines_when_citizen_deleted()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE fine
    SET status = 'cancelled',
        updated_at = CURRENT_TIMESTAMP
    WHERE citizen_id = OLD.id
      AND status = 'pending';

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
