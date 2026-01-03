CREATE TABLE IF NOT EXISTS notification (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_method (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_user (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citizen (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    app_user_id INTEGER NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT NOT NULL,
    biometric_reference JSONB,
    wallet_balance NUMERIC(10,2) DEFAULT 0.00,
    debt NUMERIC(10,2) DEFAULT 0.00,
    allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT cpf CHECK (length(cpf) = 11),
    CONSTRAINT birth_date CHECK (birth_date <= CURRENT_DATE),
    CONSTRAINT email CHECK (email LIKE '%_@_%._%'),
    CONSTRAINT chk_wallet_balance CHECK (wallet_balance >= 0),
    CONSTRAINT chk_debt CHECK (debt >= 0),
    CONSTRAINT fk_user
      FOREIGN KEY (app_user_id)
      REFERENCES app_user(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sensor (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    app_user_id INTEGER NOT NULL,
    model VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    location TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    last_reading JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user
      FOREIGN KEY (app_user_id)
      REFERENCES app_user(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicle (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    app_user_id INTEGER NOT NULL,
    license_plate VARCHAR(12) UNIQUE NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    citizen_id INTEGER,
    allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_citizen
      FOREIGN KEY (citizen_id)
      REFERENCES citizen(id)
      ON DELETE SET NULL,
    CONSTRAINT fk_user
      FOREIGN KEY (app_user_id)
      REFERENCES app_user(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reading (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    value JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sensor
      FOREIGN KEY (sensor_id)
      REFERENCES sensor(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicle_citizen (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_id INTEGER NOT NULL,
    citizen_id INTEGER NOT NULL,
    UNIQUE (vehicle_id, citizen_id),
    CONSTRAINT fk_vehicle
      FOREIGN KEY (vehicle_id)
      REFERENCES vehicle(id)
      ON DELETE CASCADE,
    CONSTRAINT fk_citizen
      FOREIGN KEY (citizen_id)
      REFERENCES citizen(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS traffic_incident (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vehicle_id INTEGER,
    sensor_id INTEGER NOT NULL,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vehicle
      FOREIGN KEY (vehicle_id)
      REFERENCES vehicle(id)
      ON DELETE SET NULL,
    CONSTRAINT fk_sensor
      FOREIGN KEY (sensor_id)
      REFERENCES sensor(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fine (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    traffic_incident_id INTEGER NOT NULL,
    citizen_id INTEGER NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_fine_amount CHECK (amount >= 0),
    CONSTRAINT chk_fine_status CHECK (
        status IN ('pending', 'paid', 'cancelled')
    ),
    CONSTRAINT fk_traffic_incident
      FOREIGN KEY (traffic_incident_id)
      REFERENCES traffic_incident(id)
      ON DELETE CASCADE,
    CONSTRAINT fk_citizen
      FOREIGN KEY (citizen_id)
      REFERENCES citizen(id)
      ON DELETE CASCADE
);  

CREATE TABLE IF NOT EXISTS fine_payment (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fine_id INTEGER NOT NULL,
    amount_paid NUMERIC(10,2) NOT NULL,
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_amount_paid CHECK (amount_paid >= 0),
    CONSTRAINT fk_fine
      FOREIGN KEY (fine_id)
      REFERENCES fine(id)
      ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS app_user_notification (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notification_id INTEGER NOT NULL,
    app_user_id INTEGER NOT NULL,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (notification_id, app_user_id),
    CONSTRAINT fk_notification
      FOREIGN KEY (notification_id)
      REFERENCES notification(id)
      ON DELETE CASCADE,
    CONSTRAINT fk_app_user
      FOREIGN KEY (app_user_id)
      REFERENCES app_user(id)
      ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    row_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    app_user_id INTEGER,
    performed_by_app_user_id INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_operation CHECK (
        operation IN ('INSERT', 'UPDATE', 'DELETE')
    ),
    CONSTRAINT fk_affected_user
      FOREIGN KEY (app_user_id)
      REFERENCES app_user(id)
      ON DELETE SET NULL,
    CONSTRAINT fk_performed_by_user
      FOREIGN KEY (performed_by_app_user_id)
      REFERENCES app_user(id)
      ON DELETE SET NULL
);

