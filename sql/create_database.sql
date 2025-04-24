/* -----------------------------------------------------------
   Create BioNet  (ejecutar en SQL Server 2022 / Express)
   Autor: Martín Vargas
------------------------------------------------------------*/
/* -------- 0. ir a master -------- */
USE master;
GO

/* -------- 1. cerrar y dropear si existe -------- */
IF DB_ID('BioNet') IS NOT NULL
BEGIN
    ALTER DATABASE BioNet SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE BioNet;
END
GO

/* -------- 2. crear de nuevo -------- */
CREATE DATABASE BioNet;
GO
USE BioNet;
GO
/* 3 ─ Tablas maestras */
CREATE TABLE laboratorios (
    laboratorio_id INT PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    ciudad         VARCHAR(80)  NOT NULL
);

CREATE TABLE pacientes (
    paciente_id      INT PRIMARY KEY,
    nombres          VARCHAR(100),
    apellidos        VARCHAR(100),
    fecha_nacimiento DATE
);

/* 4 ─ Tabla fact resultados + restricciones */
CREATE TABLE resultados_examenes (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    laboratorio_id  INT         NOT NULL,
    paciente_id     INT         NOT NULL,
    tipo_examen     VARCHAR(50) NOT NULL,
    resultado       VARCHAR(50) NOT NULL,
    fecha_examen    DATE        NOT NULL,
    CONSTRAINT uq_resultado UNIQUE
        (laboratorio_id, paciente_id, tipo_examen, fecha_examen),
    CONSTRAINT fk_res_lab FOREIGN KEY (laboratorio_id)
        REFERENCES laboratorios(laboratorio_id),
    CONSTRAINT fk_res_pac FOREIGN KEY (paciente_id)
        REFERENCES pacientes(paciente_id)
);

/* 5 ─ Tabla de auditoría */
CREATE TABLE log_cambios_resultados (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    operacion    VARCHAR(10) NOT NULL,
    paciente_id  INT         NOT NULL,
    tipo_examen  VARCHAR(50) NOT NULL,
    fecha        DATETIME    NOT NULL DEFAULT SYSDATETIME()
);

/* 6 ─ Trigger AFTER INSERT / UPDATE */
GO
CREATE TRIGGER trg_audit_resultados
ON resultados_examenes
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO log_cambios_resultados (operacion, paciente_id, tipo_examen)
    SELECT
        CASE WHEN EXISTS (SELECT * FROM deleted) THEN 'UPDATE' ELSE 'INSERT' END,
        i.paciente_id,
        i.tipo_examen
    FROM inserted i;
END
GO

/* 7 ─ Datos maestros mínimos para pruebas */
INSERT laboratorios (laboratorio_id,nombre,ciudad) VALUES
 (101,'Lab Quito','Quito'),
 (202,'Lab Guayaquil','Guayaquil');

INSERT pacientes (paciente_id,nombres,apellidos,fecha_nacimiento) VALUES
 (1001,'Paciente','Uno','1990-01-01'),
 (1002,'Paciente','Dos','1992-03-04'),
 (1003,'Paciente','Tres','1995-05-06'),
 (2001,'Paciente','Cuatro','1989-07-08'),
 (2002,'Paciente','Cinco','1991-09-10'),
 (2003,'Paciente','Seis','1993-11-12');
GO

