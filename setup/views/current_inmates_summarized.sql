-- View: jaildata.current_inmates_summarized

-- DROP VIEW jaildata.current_inmates_summarized;

CREATE OR REPLACE VIEW jaildata.current_inmates_summarized
 AS
 SELECT a.defendant_id,
    min(a.name) AS name,
    min(a.age) AS age,
    min(a.gender::text) AS gender,
    min(a.race::text) AS race,
    max(defs.level) AS rank,
    min(
        CASE
            WHEN a.status = 'PRE-TRIAL'::text AND a.bond_status::text = 'ACTI'::text OR a.status IS NULL AND a.bond_status::text = 'ACTI'::text THEN 1
            ELSE 0
        END) AS is_pretrial,
    max(defs.violent) AS violent,
    max(defs.dwi) AS dwi,
    max(defs.violation) AS violation,
    max(defs.not_primary_custodian) AS not_primary_custodian
   FROM ( SELECT d.id,
            d.name,
            d.age,
            d.gender,
            d.race,
            c.defendant_id,
            c.charge,
            c.description,
            c.status,
            c.bond_type,
            c.bond_status,
            c.bond_amount
           FROM daily_inmates d
             LEFT JOIN daily_charges c ON d.id = c.defendant_id
          WHERE d.import_date = CURRENT_DATE) a
     LEFT JOIN charge_definitions defs ON a.charge = defs.charge AND a.description = defs.description
  GROUP BY a.defendant_id;

ALTER TABLE jaildata.current_inmates_summarized
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.current_inmates_summarized TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.current_inmates_summarized TO u3qe7k9o5epmig;

