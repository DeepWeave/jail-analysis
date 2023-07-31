-- View: jaildata.daily_charges_coded

-- DROP VIEW jaildata.daily_charges_coded;

CREATE OR REPLACE VIEW jaildata.daily_charges_coded
 AS
 SELECT daily.defendant_id,
    daily.charge,
    daily.description,
    daily.status,
    daily.docket_number,
    daily.bond_type,
    daily.bond_status,
    daily.bond_amount,
    defs.level AS rank,
    defs.class AS level,
    defs.violent,
    defs.dwi,
    defs.violation,
    defs.not_primary_custodian,
        CASE
            WHEN daily.status = 'PRE-TRIAL'::text AND daily.bond_status::text = 'ACTI'::text OR daily.status IS NULL AND daily.bond_status::text = 'ACTI'::text THEN 1
            ELSE 0
        END AS is_pretrial
   FROM daily_charges daily
     LEFT JOIN charge_definitions defs ON daily.charge = defs.charge AND daily.description = defs.description;

ALTER TABLE jaildata.daily_charges_coded
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.daily_charges_coded TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.daily_charges_coded TO u3qe7k9o5epmig;

