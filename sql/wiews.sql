CREATE VIEW citizen_active AS
SELECT *
FROM citizen
WHERE deleted_at IS NULL;

CREATE VIEW vehicle_active AS
SELECT *
FROM vehicle
WHERE deleted_at IS NULL;

CREATE VIEW sensor_active AS
SELECT *
FROM sensor
WHERE deleted_at IS NULL;

CREATE VIEW app_user_active AS
SELECT *
FROM app_user
WHERE deleted_at IS NULL;