-- View: jaildata.stays_summarized

-- DROP VIEW jaildata.stays_summarized;

CREATE OR REPLACE VIEW jaildata.stays_summarized
 AS
 SELECT stays.defendant_id,
    stays.name,
    stays.gender,
    stays.race,
    stays.start_date,
    stays.end_date,
        CASE
            WHEN stays.end_date IS NOT NULL THEN date_part('day'::text, stays.end_date::timestamp without time zone - stays.start_date::timestamp without time zone) + 1::double precision
            ELSE date_part('day'::text, CURRENT_DATE::timestamp without time zone - stays.start_date::timestamp without time zone) + 1::double precision
        END AS days,
    charges.rank,
    charges.is_pretrial,
    charges.is_violent,
    charges.is_dwi,
    charges.not_primary_custodian,
    charges.is_violation,
    stays.use_flag
   FROM ( SELECT stays_tmp.id,
            stays_tmp.defendant_id,
            stays_tmp.name,
            stays_tmp.gender,
            stays_tmp.race,
            stays_tmp.start_date,
            stays_tmp.end_date,
            stays_tmp.use_flag
           FROM stays stays_tmp) stays
     LEFT JOIN ( SELECT a.defendant_id,
            a.rank,
            a.is_pretrial,
            a.is_violent,
            a.is_dwi,
            a.is_violation,
            a.not_primary_custodian
           FROM ( SELECT daily.defendant_id,
                    max(defs.level) AS rank,
                    min(
                        CASE
                            WHEN daily.status = 'PRE-TRIAL'::text AND daily.bond_status::text = 'ACTI'::text OR daily.status IS NULL AND daily.bond_status::text = 'ACTI'::text THEN 1
                            ELSE 0
                        END) AS is_pretrial,
                    max(defs.violent) AS is_violent,
                    max(defs.dwi) AS is_dwi,
                    max(defs.violation) AS is_violation,
                    max(defs.not_primary_custodian) AS not_primary_custodian
                   FROM daily_charges daily
                     LEFT JOIN charge_definitions defs ON daily.charge = defs.charge AND daily.description = defs.description
                  GROUP BY daily.defendant_id) a) charges ON stays.defendant_id = charges.defendant_id;

ALTER TABLE jaildata.stays_summarized
    OWNER TO u3qe7k9o5epmig;

GRANT SELECT ON TABLE jaildata.stays_summarized TO cameronhenshaw;
GRANT ALL ON TABLE jaildata.stays_summarized TO u3qe7k9o5epmig;

